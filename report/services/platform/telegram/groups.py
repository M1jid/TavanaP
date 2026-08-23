from fastapi import HTTPException
from typing import List

from app.startup import minio_handler, elastic_handler
from app.config import TELEGRAM_INDEX_GROUPS as INDEX_GROUPS
from app.config import TELEGRAM_INDEX_CHANNELS as INDEX_CHANNELS
from app.config import TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES
from app.config import MINIO_TELEGRAM_GROUP_BUCKET_NAME as BUCKET_NAME

from services.platform.telegram import channels as channels_service

# Logging
import logging
logger = logging.getLogger(__name__)


def get_group_image_url(group_id: int) -> str:
    return minio_handler.generate_presigned_url(bucket_name=BUCKET_NAME, object_name=f'{group_id}.jpg')


async def get_groups_list(size: int = 40, scroll_id: str = None, search: str = None):
    if scroll_id:
        response = await elastic_handler.search_scroll(index_name=INDEX_GROUPS, size=size, scroll_id=scroll_id, scroll="2m")
    if not scroll_id or not response:
        payload = {
            "_source": ["TITLE", "PEER_ID", "URL", "FOLLOWERS", "TAG", "AVAILABLE_REACTIONS", "DESCRIPTION", "LINKED_CHANNEL_TITLE", "LINKED_CHANNEL_ID", "LINKED_CHANNEL_USERNAME", "USERNAME"],
                "sort": [
                    {
                        "FOLLOWERS.FOLLOWERS": {
                            "order": "desc"
                    }
                }
            ]
        }
        if search and isinstance(search, int):
            payload['query'] = {
                "match_phrase": {"PEER_ID": search}
            }
        elif search and isinstance(search, str):
            payload['query'] = {
                "bool": {
                    "should": [
                        {"match_phrase": {"TITLE": search}},
                        {"match_phrase": {"USERNAME": search}},
                        {"match_phrase": {"DESCRIPTION": search}},
                    ]
                }
            }
        response = await elastic_handler.search_scroll(index_name=INDEX_GROUPS, size=size, body=payload, scroll="1m")
    if not response:
        raise HTTPException(status_code=404, detail="No channels found")
    entities = response.get("hits", {}).get("hits", [])
    for entity in entities:
        if 'PEER_ID' not in entity['_source']:
            logger.error(f"PEER_ID not found in channel: {entity['_source']}")
            continue
    return {
        "scroll_id": response.get("_scroll_id"),
        "entities": [{**entity['_source'], 'IMG': get_group_image_url(entity['_source']['PEER_ID'])} for entity in entities],
    }


async def get_groups_underfollow_details(following_groups: List[int]):
    result = []
    for group_id in following_groups:
        group = await elastic_handler.get_document_by_id(index_name=INDEX_GROUPS, document_id=group_id)
        if not group:
            group = await elastic_handler.get_document_by_id(index_name=INDEX_CHANNELS, document_id=group_id)
        if not group:
            continue
        group['IMG'] = get_group_image_url(group_id)
        result.append(group)
    return result


async def get_group_details(
    group_id: int,
):
    # Get group image URL
    image_url = get_group_image_url(group_id)

    # Get group info from groups index    
    group_info = await elastic_handler.get_document_by_id(index_name=INDEX_GROUPS, document_id=group_id)
    if not group_info:
        group_info = await elastic_handler.get_document_by_id(index_name=INDEX_CHANNELS, document_id=group_id)
    if not group_info:
        raise HTTPException(status_code=404, detail="Group not found")

    group_info["IMG"] = image_url

    # Build query to get group details
    query = {
        "bool": {
            "must": [
                {"term": {"PEER_ID": group_id}},
                {"match_phrase": {"TYPE": "CHANNELCOMMENT"}}
            ]
        }
    }

    # Get message statistics
    stats_query = {
        "size": 0,
        "query": query,
        "aggs": {
            "total_messages": {"value_count": {"field": "MESSAGE_ID"}},
            "total_views": {"sum": {"field": "VIEWS_COUNT"}},
            "total_reactions": {"sum": {"field": "REACTIONS_COUNT"}},
            "total_forwards": {"sum": {"field": "FORWARDS_COUNT"}},
            "total_replies": {"sum": {"field": "REPLIES_COUNT"}}
        }
    }

    stats_response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=stats_query)
    aggs = stats_response.get("aggregations", {})
    
    return {
        "group_info": group_info,
        "statistics": {
            "total_messages": aggs.get("total_messages", {}).get("value", 0),
            "total_views": aggs.get("total_views", {}).get("value", 0),
            "total_reactions": aggs.get("total_reactions", {}).get("value", 0),
            "total_forwards": aggs.get("total_forwards", {}).get("value", 0),
            "total_replies": aggs.get("total_replies", {}).get("value", 0)
        }
    }

async def get_group_details_overview(group_id: int):
    group_info = await elastic_handler.get_document_by_id(index_name=INDEX_GROUPS, document_id=group_id)
    if group_info:
        group_info["IMG"] = get_group_image_url(group_id)
        return group_info
    group_info = await elastic_handler.get_document_by_id(index_name=INDEX_CHANNELS, document_id=group_id)
    if group_info:
        group_info["IMG"] = channels_service.get_channel_image_url(group_id)
        return group_info


async def get_group_messages(
    size: int,
    page: int,
    selected_groups: List[int],
    start_date: str,
    end_date: str,
    search_text: str,
    sentiment: str,
):
    payload = {
        "size": size,
        "from": (page-1)*size,
        "track_total_hits": True,
        "sort": [
            {"DATE": {"order": "desc"}}
        ],
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                {
                                    "match_phrase": {"TYPE": "GROUPPOST"}
                                },
                                {
                                    "match_phrase": {"TYPE": "CHANNELCOMMENT"}
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        }
    }

    if start_date and end_date:
        payload['query']['bool']['must'].append(
            {
                'range': {
                    'DATE': {
                        "gte": start_date,
                        "lte": end_date,
                    }
                }
            }
        )

    if selected_groups:
        payload['query']['bool']['must'].append(
            {
                'terms': {
                    'PEER_ID': selected_groups
                }
            }
        )

    if search_text:
        payload['query']['bool']['must'].append(
            {
                'match_phrase': {
                    'MESSAGE': search_text
                }
            }
        )

    if sentiment:
        payload['query']['bool']['must'].append(
            {
                'match_phrase': {
                    'SENTIMENT': sentiment
                }
            }
        )

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    messages = [message['_source'] for message in response['hits']['hits']]

    for message in messages:
        image_url = get_group_image_url(message['PEER_ID'])
        message['IMG'] = image_url

    return {
        'messages': messages,
        'total_messages': response['hits']['total']['value'],
        'has_more': response['hits']['total']['value'] > len(messages)
    }
