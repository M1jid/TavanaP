from fastapi import HTTPException, UploadFile
from typing import List
from services import services
from queries.queries import QueryTypes
from utils import db_handler as db

from app.startup import elastic_handler, kafka_producer, minio_handler
from app.config import TELEGRAM_INDEX_USERS as INDEX_USERS
from app.config import TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES
from app.config import MINIO_TELEGRAM_USER_BUCKET_NAME as USER_BUCKET_NAME
from app.config import MINIO_TELEGRAM_MEDIA_CHATS_BUCKET_NAME as MEDIA_CHATS_BUCKET_NAME
from app.config import TELEGRAM_INDEX_CHANNELS as INDEX_CHANNELS
from app.config import TELEGRAM_INDEX_CHAT_MESSAGES as INDEX_CHAT_MESSAGES
from app.config import TELEGRAM_CHATS_MESSAGE_SEND_TOPIC

from services.platform.telegram import channels as channels_service

# Logging
import logging
logger = logging.getLogger(__name__)


def get_user_image_url(user_id: int) -> str:
    return minio_handler.generate_presigned_url(bucket_name=USER_BUCKET_NAME, object_name=f'{user_id}.jpg')


async def get_users_list(size: int = 40, scroll_id: str = None, search: str = None):
    if scroll_id:
        response = await elastic_handler.search_scroll(index_name=INDEX_USERS, size=size, scroll_id=scroll_id, scroll="2m")
    if not scroll_id or not response:
        payload = {
            "_source": ["PHONE", "USER_ID", "BIO", "USERNAME", "LAST_NAME", "FIRST_NAME", "PERSONAL_CHANNEL_TITLE", "BIRTHDAY"],
        }
        if search:
            payload['query'] = {
                "bool": {
                    "should": [
                        {"match_phrase": {"USER_ID": search}},
                        {"match_phrase": {"USERNAME": search}},
                        {"match_phrase": {"FIRST_NAME": search}},
                        {"match_phrase": {"LAST_NAME": search}},
                        {"match_phrase": {"BIO": search}},
                    ]
                }
            }
        response = await elastic_handler.search_scroll(index_name=INDEX_USERS, size=size, body=payload, scroll="1m")
    if not response:
        raise HTTPException(status_code=404, detail="No users found")
    entities = response.get("hits", {}).get("hits", [])
    for entity in entities:
        if 'USER_ID' not in entity['_source']:
            logger.error(f"USER_ID not found in user: {entity['_source']}")
            continue
    return {
        "scroll_id": response.get("_scroll_id"),
        "entities": [{**entity['_source'], 'IMG': get_user_image_url(entity['_source']['USER_ID'])} for entity in entities],
    }


async def get_users_underfollow_details(following_users: List[int]):
    result = []
    for user_id in following_users:
        user = await elastic_handler.get_document_by_id(index_name=INDEX_USERS, document_id=user_id)
        if not user:
            continue
        user['IMG'] = get_user_image_url(user_id)
        result.append(user)
    return result


async def get_user_details(
    user_id: int,
):
    user_info = await elastic_handler.get_document_by_id(index_name=INDEX_USERS, document_id=user_id)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    # Get channel image URL
    image_url = get_user_image_url(user_id)
    user_info["IMG"] = image_url

    # Build query to get user messages
    query = {
        "bool": {
            "must": [
                {"match": {"AUTHOR_ID": user_id}},
                {"match": {"TYPE": "CHANNELCOMMENT"}},
                {"match": {"AUTHOR_TYPE": "USER"}}
            ]
        }
    }

    # Get user statistics
    stats_query = {
        "size": 0,
        "query": query,
        "aggs": {
            "total_messages": {"value_count": {"field": "MESSAGE_ID"}},
            "total_reactions": {"sum": {"field": "REACTIONS_COUNT"}},
            "total_replies": {"sum": {"field": "REPLIES_COUNT"}},
            "sentiment": {"terms": {"field": "SENTIMENT.keyword"}},
            "sense": {"terms": {"field": "SENSE.keyword"}},
            "tags": {"terms": {"field": "TAGS.keyword"}},
            "history": {"date_histogram": {"field": "DATE", "calendar_interval": "day"}},
        }
    }

    stats_response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=stats_query)
    aggs = stats_response.get("aggregations", {})

    return {
        "user_info": user_info,
        "statistics": {
            "total_messages": aggs.get("total_messages", {}).get("value", 0),
            "total_reactions": aggs.get("total_reactions", {}).get("value", 0),
            "total_replies": aggs.get("total_replies", {}).get("value", 0),
            "sentiment": aggs.get("sentiment", {}).get("buckets", []),
            "sense": aggs.get("sense", {}).get("buckets", []),
            "tags": aggs.get("tags", {}).get("buckets", []),
            "history": aggs.get("history", {}).get("buckets", []),
        }
    }

async def get_user_details_overview(user_id: int):
    user_info = await elastic_handler.get_document_by_id(index_name=INDEX_USERS, document_id=user_id)
    if user_info:
        user_info["IMG"] = get_user_image_url(user_id)
        return user_info
    return None

async def get_user_messages(
    size: int,
    page: int,
    selected_users: List[int],
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
                "must": [{"match_phrase": {"TYPE": "CHANNELCOMMENT"}}]
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

    if selected_users:
        payload['query']['bool']['must'].append(
            {
                'terms': {
                    'AUTHOR_ID': [int(peer_id) for peer_id in selected_users]
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
        image_url = get_user_image_url(message['AUTHOR_ID'])
        message['IMG'] = image_url

    return {
        'messages': messages,
        'total_messages': response['hits']['total']['value'],
        'has_more': response['hits']['total']['value'] > len(messages)
    }

async def get_messages_details(
    private_url: str,
):
    message = await elastic_handler.get_document_by_id(index_name=INDEX_MESSAGES, document_id=private_url)
    image_url = get_user_image_url(message['AUTHOR_ID'])
    message['IMG'] = image_url
    root_message = None
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    reply_link = message['PUBLIC_URL']
    if '?comment=' in reply_link:
        reply_link = reply_link.split('?comment=')[0]
        payload = {
            "size": 10000,
            "track_total_hits": True,
            "query": {
                "match_phrase": {
                    "PUBLIC_URL": reply_link
                }
            }
        }
        response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
        response = response['hits']['hits']
        if response:
            root_message = response[0]['_source']
            root_message['IMG'] = get_user_image_url(root_message['PEER_ID'])

    return {
        "message": message,
        "root_message": root_message
    }


async def get_user_joined_channels(user_id: int):
    template = services.jinja_template_generator(path=QueryTypes.TelegramUserJoinedChannels)

    payload = template.render(
        user_id=user_id,
    )

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    result = []
    for peer_id in response['aggregations']['PEER_ID']['buckets']:
        payload = {
            "size": 1,
            "query": {
                "match_phrase": {
                    "LINKED_GROUP_ID": peer_id['key']
                }
            }
        }
        channel_info = await elastic_handler.client.search(index=INDEX_CHANNELS, body=payload)
        channel_info = channel_info['hits']['hits'][0]['_source']
        channel_info['IMG'] = channels_service.get_channel_image_url(channel_info['PEER_ID'])
        result.append(channel_info)
    return result
