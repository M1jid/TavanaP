import logging
import difflib
import json
import copy
import asyncio

from fastapi import HTTPException, status
from typing import List
from collections import defaultdict
from datetime import datetime

from app.startup import minio_handler
from app.startup import elastic_handler

from utils import db_handler as db
from utils.raw_subscribers_aja_channels import RAW_SUBSCRIBERS
from utils.routing_roles import config as routing_roles

from app.config import TELEGRAM_INDEX_CHANNELS as INDEX_CHANNELS
from app.config import TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES
from app.config import TELEGRAM_INDEX_GROUPS as INDEX_GROUPS
from app.config import MINIO_TELEGRAM_CHANNEL_BUCKET_NAME as BUCKET_NAME

from queries.queries import QueryTypes

from services import services
from services.platform.telegram import groups as groups_service

from keywords.filter_forces import forces
from keywords.filter_topics import topics
from keywords.filter_persons import persons
from keywords.filter_events import events

logger = logging.getLogger(__name__)
BASE_KEYWORDS_DIR = "/code/keywords/telegram"


def get_channel_image_url(channel_id: int) -> str:
    return minio_handler.generate_presigned_url(bucket_name=BUCKET_NAME, object_name=f'{channel_id}.jpg')


async def get_channels_list(size: int = 40, scroll_id: str = None, search: str = None):
    if scroll_id:
        response = await elastic_handler.search_scroll(index_name=INDEX_CHANNELS, size=size, scroll_id=scroll_id, scroll="2m")
    if not scroll_id or not response:
        payload = {
            "_source": ["TITLE", "PEER_ID", "URL", "FOLLOWERS", "TAG", "AVAILABLE_REACTIONS", "DESCRIPTION", "LINKED_GROUP_TITLE", "LINKED_GROUP_ID", "LINKED_GROUP_USERNAME", "USERNAME"],
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
        response = await elastic_handler.search_scroll(index_name=INDEX_CHANNELS, size=size, body=payload, scroll="1m")
    if not response:
        raise HTTPException(status_code=404, detail="No channels found")
    entities = response.get("hits", {}).get("hits", [])
    for entity in entities:
        if 'PEER_ID' not in entity['_source']:
            logger.error(f"PEER_ID not found in channel: {entity['_source']}")
            continue
    return {
        "scroll_id": response.get("_scroll_id"),
        "entities": [{**entity['_source'], 'IMG': get_channel_image_url(entity['_source']['PEER_ID'])} for entity in entities],
    }


async def get_channels_underfollow_details(following_channels: List[int]):
    result = []
    for channel_id in following_channels:
        channel = await elastic_handler.get_document_by_id(index_name=INDEX_CHANNELS, document_id=channel_id)
        if not channel:
            continue
        channel['IMG'] = get_channel_image_url(channel_id)
        result.append(channel)
    return result


async def get_channel_underfollow(channel_id: int) -> dict:
    if not channel_id:
        raise HTTPException(status_code=400, detail="Channel ID is required")
    if channel_id:
        channel = db.get_telegram_channel_by_id(channel_id)
        if channel:
            channel_id = channel['id']
        else:
            raise HTTPException(status_code=404, detail="Channel not found")
    return db.get_channel_underfollow(channel_id)


async def delete_channel_underfollow(channel_id: int) -> dict:
    if not channel_id:
        raise HTTPException(status_code=400, detail="Channel ID is required")
    if channel_id:
        channel = db.get_telegram_channel_by_id(channel_id)
        if channel:
            channel_id = channel['id']
        else:
            raise HTTPException(status_code=404, detail="Channel not found")
    return db.delete_channel_underfollow(channel_id)


async def create_channel_underfollow(data) -> dict:
    logger.info(data)
    if not data.channel_id:
        raise HTTPException(status_code=400, detail="Channel ID is required")
    if data.channel_id:
        channel = db.get_telegram_channel_by_id(data.channel_id)
        if channel:
            data.channel_id = channel['id']
        else:
            raise HTTPException(status_code=404, detail="Channel not found")
    # Convert Pydantic model to dict if needed
    if hasattr(data, 'model_dump'):
        data_dict = data.model_dump(mode='json')
    elif hasattr(data, 'dict'):
        data_dict = data.dict()
    else:
        data_dict = data
    return db.create_channel_underfollow(data_dict)


async def update_channel_underfollow(channel_id: int, data) -> dict:
    # Convert Pydantic model to dict if needed
    if hasattr(data, 'model_dump'):
        data_dict = data.model_dump(mode='json')
    elif hasattr(data, 'dict'):
        data_dict = data.dict()
    else:
        data_dict = data
    return db.update_channel_underfollow(channel_id, data_dict)


async def get_channel_details(channel_id: int) -> dict:
    # Get channel info from channels index    
    channel_info = await elastic_handler.get_document_by_id(index_name=INDEX_CHANNELS, document_id=channel_id)
    if not channel_info:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Get channel image URL
    image_url = get_channel_image_url(channel_id)
    channel_info["IMG"] = image_url

    # Build query to get channel details
    query = {
        "bool": {
            "must": [
                {"term": {"PEER_ID": channel_id}},
                {"match_phrase": {"TYPE": "CHANNELPOST"}}
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
        "channel_info": channel_info,
        "statistics": {
            "total_messages": aggs.get("total_messages", {}).get("value", 0),
            "total_views": aggs.get("total_views", {}).get("value", 0),
            "total_reactions": aggs.get("total_reactions", {}).get("value", 0),
            "total_forwards": aggs.get("total_forwards", {}).get("value", 0),
            "total_replies": aggs.get("total_replies", {}).get("value", 0),
            "sentiment": aggs.get("sentiment", {}).get("buckets", []),
            "sense": aggs.get("sense", {}).get("buckets", []),
            "tags": aggs.get("tags", {}).get("buckets", []),
            "history": aggs.get("history", {}).get("buckets", []),
        }
    }


async def get_channel_details_overview(channel_id: int):
    channel_info = await elastic_handler.get_document_by_id(index_name=INDEX_CHANNELS, document_id=channel_id)
    if channel_info:
        channel_info["IMG"] = get_channel_image_url(channel_id)
        return channel_info
    channel_info = await elastic_handler.get_document_by_id(index_name=INDEX_GROUPS, document_id=channel_id)
    if channel_info:
        channel_info["IMG"] = get_channel_image_url(channel_id)
        return channel_info
    return None


async def get_channels_overview(
    channel_ids: list[int],
):
    should_terms = [{"term": {"_id": str(cid)}} for cid in channel_ids]

    payload = {
        "query": {
            "bool": {
                "should": should_terms,
                "minimum_should_match": 1
            }
        },
        "size": len(channel_ids)
    }

    response = await elastic_handler.client.search(index=INDEX_CHANNELS, body=payload)

    hits = response.get("hits", {}).get("hits", [])
    for hit in hits:
        hit["_source"]["IMG"] = get_channel_image_url(hit["_id"])
    return {hit["_id"]: hit["_source"] for hit in hits}


async def get_channel_messages(
    size: int,
    page: int,
    selected_channels: List[int],
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
                "must": [{"match_phrase": {"TYPE": "CHANNELPOST"}}]
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

    if selected_channels:
        payload['query']['bool']['must'].append(
            {
                'terms': {
                    'PEER_ID': selected_channels
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
        image_url = get_channel_image_url(message['PEER_ID'])
        message['IMG'] = image_url

    return {
        'messages': messages,
        'total_messages': response['hits']['total']['value'],
        'has_more': response['hits']['total']['value'] > len(messages)
    }


async def get_channel_comments(
    size: int,
    page: int,
    selected_channels: List[int],
    start_date: str,
    end_date: str,
    search_text: str,
):
    payload = {
        "size": size,
        "from": (page-1)*size,
        "track_total_hits": True,
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

    if selected_channels:
        payload['query']['bool']['must'].append(
            {
                'terms': {   
                    'PEER_ID': selected_channels
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

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    messages = [doc['_source'] for doc in response['hits']['hits']]
    for message in messages:
        image_url = get_channel_image_url(message['PEER_ID'])
        message['IMG'] = image_url
    return messages


async def get_message_details(
    private_url: str,
):
    logger.info(f"Getting message details for {private_url}")
    message = await elastic_handler.get_document_by_id(index_name=INDEX_MESSAGES, document_id=private_url)
    image_url = get_channel_image_url(message['PEER_ID'])
    message['IMG'] = image_url
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    payload = {
        "size": 100,
        "track_total_hits": True,
        "query": {
            "match_phrase": {
                "PUBLIC_URL": message['PUBLIC_URL']
            }
        }
    }
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    replies = [doc['_source'] for doc in response['hits']['hits']]
    if not replies or len(replies) < 2:
        replies = []
    for reply in replies:
        if reply['PEER_ID'] == message['PEER_ID']:
            reply['IMG'] = message['IMG']
        else:
            image_url = get_channel_image_url(reply['PEER_ID'])
            reply['IMG'] = image_url
    return {
        "message": message,
        "replies": replies
    }


async def get_owned_channels():
    """Get Telegram owned channels"""
    return [{'name': conf['name'], 'id': abs(conf['channel_id'])} for conf in routing_roles]


async def get_owned_channels_report(channel_id: int, start_date: str, end_date: str, size: int = 12, page: int = 1):
    """Get Telegram owned channels report"""
    channel = [channel for channel in routing_roles if abs(channel['channel_id']) == channel_id]
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    channel = channel[0]
    roles = channel['roles']
    channel_id = str(channel['channel_id'])[1:]
    channel_name = channel['name']
    conditions = []

    for role in roles:
        must = [{"match_phrase": {"MESSAGE": term}} for term in role["must"]]
        should = [{"match_phrase": {"MESSAGE": term}} for term in role["should"]]
        must_not = [{"match_phrase": {"MESSAGE": term}} for term in role["must_not"]]
        
        # Only add condition if there's at least one clause
        if must or should or must_not:
            condition = {"bool": {}}
            
            if must:
                condition["bool"]["must"] = must
            if should:
                condition["bool"]["should"] = should
                condition["bool"]["minimum_should_match"] = 1
            if must_not:
                condition["bool"]["must_not"] = must_not
                
            conditions.append(condition)

    template = services.jinja_template_generator(path=QueryTypes.TelegramOwnedChannelsReport)
    payload = template.render(
        start_date=start_date,
        end_date=end_date,
        conditions=conditions,
        size=size,
        page=(page-1)*size
    )
    payload = json.loads(payload)
    payload['query']['bool']['must'][1]['bool']['should'] = payload['query']['bool']['must'][1]['bool']['should'][0]
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    return {
        'name': channel_name,
        'id': channel_id,
        'total_docs': response['hits']['total']['value'],
        'stats': {
            'reactions': response['aggregations']['REACTIONS_COUNT']['value'],
            'forwards': response['aggregations']['FORWARDS_COUNT']['value'],
            'comments': response['aggregations']['REPLIES_COUNT']['value'],
            'views': response['aggregations']['VIEWS_COUNT']['value'],
        },
        'reactionsBreakdown': {r.get("key"): r.get("doc_count", 0) for r in response.get('aggregations', {}).get('reactionsBreakdown', {}).get('buckets', [])},
        'history': [day['doc_count'] for day in response['aggregations']['HISTORY']['buckets']],
        'sentiment': {sense["key"]: sense['doc_count'] for sense in response['aggregations']["SENTIMENT"]["buckets"]},
        'sense': {sense["key"]: sense['doc_count'] for sense in response['aggregations']["SENSE"]["buckets"]},
        'TOP_POSTS': [post['_source'] for post in response['aggregations']['TOP_POSTS']['hits']['hits']],
    }


async def get_sourcetracing(
    search_text: str,
    start_date: str,
    end_date: str,
    size: int = 10,
) -> list[dict]:
    template = services.jinja_template_generator(path=QueryTypes.TelegramSourceTracing)
    payload = template.render(
        search_text=search_text,
        start_date=start_date,
        end_date=end_date,
        size=size
    )

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    hits = response["hits"]["hits"]
    
    result = []
    for hit in hits:
        try:
            channel_details = await get_channel_details(hit["_source"]["PEER_ID"])
        except Exception as e:
            logger.error(f"Channel not found for {hit['_source']['PEER_ID']}")
            continue
        result.append({
            "post_text": hit["_source"]["MESSAGE"],
            "date": hit["_source"]["DATE"],
            "channel_username": channel_details['channel_info']['USERNAME'],
            "channel_img": get_channel_image_url(hit["_source"]["PEER_ID"])
        })
    
    return result


async def get_insights(
    search_text: str,
    size: int = 10,
) -> list[dict]:
    template = services.jinja_template_generator(path=QueryTypes.TelegramChannelInsights)
    payload = template.render(
        search_text=search_text,
        size=size
    )
    
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    buckets = response.get("aggregations", {}).get("channels", {}).get("buckets", [])
    channel_ids = [str(bucket["key"]) for bucket in buckets]
    channel_info_map = await get_channels_overview(channel_ids)
    result = {}

    for bucket in buckets:
        cid = str(bucket["key"])
        sentiment_buckets = bucket.get("dominant_sentiment", {}).get("buckets", [])
        sentiment_key = sentiment_buckets[0]["key"] if sentiment_buckets else "نامشخص"

        channel_info = channel_info_map.get(cid, {})
        username = channel_info.get("USERNAME", "")

        channel_data = {
            "channel_id": cid,
            "channel_username": username,
            "channel_img": get_channel_image_url(channel_id=cid)
        }

        if sentiment_key not in result:
            result[sentiment_key] = []
        result[sentiment_key].append(channel_data)

    return result


async def get_similar_channels(
    search_text: str,
    start_date: str,
    end_date: str,
    size: int = 10,
    sort: str = "VIEWS"
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramSimilarChannels)
    payload = json.loads(template.render(
        search_text=search_text,
        start_date=start_date,
        end_date=end_date,
        size=size
    ))

    if sort == "DATE":
        payload['sort'] = [
            {"DATE": {"order": "asc"}}
        ]
    elif sort == "VIEWS":
        payload['sort'] = [
            {"VIEWS_COUNT": {"order": "desc"}}
        ]
    else:
        raise HTTPException(status_code=400, detail="Invalid sort value")

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    hits = response.get("hits", {}).get("hits", [])

    if not hits:
        return {
            "main_message": None,
            "similar_messages": []
        }

    main_hit = hits[0]
    main_message = main_hit["_source"]["MESSAGE"]
    main_channel_id = str(main_hit["_source"]["PEER_ID"])
    main_date = main_hit["_source"].get("DATE", "")
    main_url = main_hit["_source"].get("PUBLIC_URL", "")

    candidates = []
    for hit in hits[1:]:
        msg = hit["_source"]["MESSAGE"]
        cid = str(hit["_source"]["PEER_ID"])
        date = hit["_source"].get("DATE", "")
        url = hit["_source"].get("PUBLIC_URL", "")
        if msg != main_message:
            candidates.append({
                "message": msg,
                "channel_id": cid,
                "date": date,
                "url": url
            })

    scored = []
    for item in candidates:
        score = difflib.SequenceMatcher(None, main_message, item["message"]).ratio()
        scored.append({
            "message": item["message"],
            "channel_id": item["channel_id"],
            "similarity": round(score, 2),
            "date": item["date"],
            "url": item["url"]
        })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    top_scored = scored[:10]

    def parse_date(d):
        try:
            return datetime.fromisoformat(d)
        except Exception:
            return datetime.min

    top_scored.sort(key=lambda x: parse_date(x["date"]))

    all_ids = list(set([main_channel_id] + [item["channel_id"] for item in top_scored]))
    channel_info_map = await get_channels_overview(all_ids)

    main_channel_name = channel_info_map.get(main_channel_id, {}).get("USERNAME", "")

    top_similar = []
    for item in top_scored:
        cid = item["channel_id"]
        channel_name = channel_info_map.get(cid, {}).get("USERNAME", "")
        top_similar.append({
            "message": item["message"],
            "channel": channel_name,
            "similarity": item["similarity"],
            "date": item["date"],
            "url": item["url"]
        })

    return {
        "main_message": {
            "message": main_message,
            "channel": main_channel_name,
            "date": main_date,
            "url": main_url
        },
        "similar_messages": top_similar
    }


async def parse_forwarding_aggregation():
    """
    Fetches top forwarded channels from Elasticsearch, then fetches actual channel info
    from a separate channels index to ensure FORWARDED_FROM_USERNAME and URL are correct.
    Cleans PUBLIC_URL so it points directly to the channel (not a post).
    """

    def clean_telegram_url(url: str) -> str:
        """Removes post number from PUBLIC_URL if exists."""
        if not url:
            return None
        parts = url.rstrip('/').split('/')
        if parts[-1].isdigit():  # آخر لینک عدد بود یعنی لینک پست
            return '/'.join(parts[:-1])
        return url
    async def get_channel_info(fwd_peer_id: int):
        """
        Fetch actual channel info from telegram-channels index.
        Returns (USERNAME, URL) or ("", None) if not found.
        """
        resp = await elastic_handler.client.search(
            index="telegram-channels",
            body={
                "query": {"term": {"PEER_ID": fwd_peer_id}},
                "_source": ["USERNAME", "URL"],
                "size": 1
            }
        )
        hits = resp.get('hits', {}).get('hits', [])
        if hits:
            username = hits[0]['_source']['USERNAME']
            url = hits[0]['_source']['URL']  # URL کانال اصلی
            image_url = get_channel_image_url(fwd_peer_id)
            return username, url ,image_url
        return "", None

    template = services.jinja_template_generator(path=QueryTypes.TelegramGetChannel)
    payload = json.loads(template.render())

    response = await elastic_handler.client.search(
        index="telegram-messages", body=payload
    )

    result = []
    for fwd_bucket in response['aggregations']['top_forwarded_channels']['buckets']:
        fwd_peer_id = fwd_bucket['key']
        total_views = fwd_bucket['total_views']['value']

        # 2️⃣ گرفتن اطلاعات واقعی کانال اصلی
        fwd_username, fwd_url_clean, image_url = await get_channel_info(fwd_peer_id)
        

        # 3️⃣ گرفتن لیست کانال‌های فوروارد کننده
        forwarding_channels = []
        for ch_bucket in fwd_bucket['forwarding_channels']['buckets']:
            ch_peer_id = ch_bucket['key']
            doc_count = ch_bucket['doc_count']
            image_url_flowing = get_channel_image_url(ch_peer_id)


            ch_sample_hits = (
                ch_bucket.get('channel_sample', {})
                         .get('hits', {})
                         .get('hits', [])
            )
            if ch_sample_hits:
                ch_url = ch_sample_hits[0]['_source']['PUBLIC_URL']
                ch_url_clean = clean_telegram_url(ch_url)
                ch_username = ch_url_clean.split('/')[-1] if ch_url_clean else ''
            else:
                ch_username = ''
                ch_url_clean = None

            forwarding_channels.append({
                "CHANNEL_ID": ch_peer_id,
                "USERNAME": ch_username,
                "PUBLIC_URL": ch_url_clean,
                "COUNT": doc_count,
                "IMG":image_url_flowing
            })

        result.append({
            "IMG":image_url,
            "FWD_PEER_ID": fwd_peer_id,
            "FORWARDED_FROM_USERNAME": fwd_username,
            "FORWARDED_FROM_URL": fwd_url_clean,
            "TOTAL_VIEWS": total_views,
            "FORWARDING_CHANNELS": forwarding_channels
        })

    return result



async def get_keyword_top_channels(
    search_text: str,
    start_date: str,
    end_date: str,
    subject_type: str,
    subject_id: int,
    size: int = 10
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramKeywordTopChannels)

    if search_text != "null":
        query_body = json.loads(template.render(
            start_date=start_date,
            end_date=end_date,
            must=[[search_text]],
            should=[[]],
            must_not=[[]]
        ))
    else:
        filter_dic = {}
        if subject_type == "topic":
            filter_dic = topics
        elif subject_type == "person":
            filter_dic = persons
        elif subject_type == "event":
            filter_dic = events
        elif subject_type == "force":
            filter_dic = forces
        else:
            raise HTTPException(status_code=400, detail="Invalid subject type")

        query_body = json.loads(template.render(
            start_date=start_date,
            end_date=end_date,
            must=filter_dic[subject_id]["must"],
            should=filter_dic[subject_id]["should"],
            must_not=filter_dic[subject_id]["must_not"]
        ))

    query_body["aggs"] = {
        "top_channels": {
            "terms": {
                "field": "PEER_ID",
                "size": size,
                "order": {"_count": "desc"}
            },
            "aggs": {
                "channel_name": {"terms": {"field": "CHANNEL_TITLE.keyword", "size": 1}},
                "channel_img": {"terms": {"field": "CHANNEL_IMG.keyword", "size": 1}}
            }
        }
    }

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=query_body)

    all_peer_ids = [bucket["key"] for bucket in response["aggregations"]["top_channels"]["buckets"]]
    channel_info = await get_channels_overview(list(all_peer_ids))

    top_channels = []
    for bucket in response["aggregations"]["top_channels"]["buckets"]:
        channel_id = bucket["key"]
        count = bucket["doc_count"]
        channel_data = channel_info.get(str(channel_id), channel_info.get(channel_id, {}))
        username = channel_data.get("USERNAME") if channel_data else ""
        img = channel_data.get("IMG") if channel_data else ""

        top_channels.append({
            "channel_id": channel_id,
            "count": count,
            "username": username,
            "img": img
        })

    return {"top_channels": top_channels}


async def get_content_report(search_text: str, start_date: str, end_date: str, size: int = 10, page: int = 1, sort: str = "VIEWS"):
    template = services.jinja_template_generator(path=QueryTypes.TelegramContentReportTags)
    payload = json.loads(template.render(
        search_text=search_text,
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=(page-1)*size
    ))

    if sort == "DATE":
        payload['sort'] = [{"DATE": {"order": "desc"}}]
    elif sort == "FORWARDS":
        payload['sort'] = [{"FORWARDS_COUNT": {"order": "desc"}}]
    elif sort == "VIEWS":
        payload['sort'] = [{"VIEWS_COUNT": {"order": "desc"}}]
    elif sort == "REACTIONS":
        payload['sort'] = [{"REACTIONS_COUNT": {"order": "desc"}}]
    elif sort == "COMMENTS":
        payload['sort'] = [{"REPLIES_COUNT": {"order": "desc"}}]

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    trends = response['aggregations']['trends']['buckets']
    all_peer_ids = set()

    for trend in trends:
        for post in trend['top_messages']['hits']['hits']:
            src = post['_source']
            peer_id = src.get('PEER_ID')
            if peer_id:
                all_peer_ids.add(int(peer_id))
    
    logger.info(all_peer_ids)
    result = []
    logger.info(trends[0])
    for trend in trends:
        top_posts = []
        for post in trend['top_messages']['hits']['hits']:
            src = post['_source']
            date_val = src.get('DATE')
            hour_val, day_val = None, None
            dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
            hour_val = dt.strftime("%H:%M")
            day_val = dt.strftime("%Y-%m-%d")

            peer_id = src['PEER_ID']
            channel_data = await get_channels_overview([peer_id])
            url = ""
            if src['TYPE'] == 'CHANNELPOST':
                url = get_channel_image_url(channel_id=int(peer_id))
            elif src['TYPE'] == 'CHANNELCOMMENT':
                url = groups_service.get_group_image_url(group_id=int(peer_id))

            top_posts.append({
                **src,
                'hour': hour_val,
                'day': day_val,
                'USERNAME': channel_data.get('USERNAME', None) if channel_data else None,
                'IMG': url,
                'REPLIES_COUNT':src.get('REPLIES_COUNT'),
                'REACTIONS_COUNT':src.get('REACTIONS_COUNT'),
                "HASHTAGS":src.get('HASHTAGS'),
                "REACTIONS":src.get('REACTIONS'),
                "PEER_ID": peer_id,
            })

        result.append({
            'id': trend['key'],
            'name': trend['key'],
            'doc_count': trend['doc_count'],
            'sentiment': max(trend["sentiment"]["buckets"], key=lambda x: x["doc_count"])["key"] if trend["sentiment"]["buckets"] else "unknown",
            'history': [time_range['doc_count'] for time_range in trend['history']['buckets']],
            'sentimentBreakdown': {sense["key"]: sense["doc_count"] for sense in trend["sentiment"]["buckets"]},
            'senseBreakdown': {sense["key"]: sense["doc_count"] for sense in trend["sense"]["buckets"]},
            'reactionsBreakdown': {r.get("key"): r.get("doc_count", 0) for r in trend["reactionsBreakdown"]["buckets"]},
            'stats': {
                'reactions': trend['reactions']['value'],
                'comments': trend['comments']['value'],
                'forwards': trend['forwards']['value'],
                'views': trend['views']['value'],
            },
            'publishers': trend['unique_channels']['value'],
            'top_posts': top_posts
        })

    return result


async def get_content_report_no_tags(
    search_text: str, 
    start_date: str, 
    end_date: str, 
    size: int = 10, 
    page: int = 1, 
    sort: str = 'VIEWS'
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramContentReportNoTags)
    payload = json.loads(template.render(
        search_text=search_text,
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=(page-1)*size
    ))

    if sort == "DATE":
        payload['sort'] = [{"DATE": {"order": "desc"}}]
    elif sort == "FORWARDS":
        payload['sort'] = [{"FORWARDS_COUNT": {"order": "desc"}}]
    elif sort == "VIEWS":
        payload['sort'] = [{"VIEWS_COUNT": {"order": "desc"}}]
    elif sort == "REACTIONS":
        payload['sort'] = [{"REACTIONS_COUNT": {"order": "desc"}}]
    elif sort == "COMMENTS":
        payload['sort'] = [{"REPLIES_COUNT": {"order": "desc"}}]

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    hits = []
    total_followers = 0
    for hit in response.get("hits", {}).get("hits", []):
        source = hit["_source"]
        peer_id = source.get("PEER_ID")
        peer_type = source.get("PEER_TYPE")

        if peer_type == "CHANNEL":
            try:
                channel_doc = await elastic_handler.get_document_by_id(index_name=INDEX_CHANNELS, document_id=peer_id)
                followers_list = channel_doc.get("FOLLOWERS")
                if isinstance(followers_list, list) and followers_list:
                    last_entry = followers_list[0]
                    if isinstance(last_entry.get("FOLLOWERS"), int):
                        total_followers += last_entry["FOLLOWERS"]
            except Exception as e:
                logger.error(f"Channel not found for '{peer_id}'")

        elif peer_type == "GROUP":
            try:
                gp_doc = await elastic_handler.get_document_by_id(index_name=INDEX_GROUPS, document_id=peer_id)
                followers_list = gp_doc.get("FOLLOWERS")
                if isinstance(followers_list, list) and followers_list:
                    last_entry = followers_list[0]
                    if isinstance(last_entry.get("FOLLOWERS"), int):
                        total_followers += last_entry["FOLLOWERS"]
            except Exception as e:
                logger.error(f"Group not found for '{peer_id}'")

        hits.append({
            "peer_type": peer_type,
            "message": source.get("MESSAGE"),
            "sentiment": source.get("SENTIMENT"),
            "sense": source.get("SENSE"),
            "forwards_count": source.get("FORWARDS_COUNT"),
            "replies_count": source.get("REPLIES_COUNT"),
            "views_count": source.get("VIEWS_COUNT"),
            "hashtags": source.get("HASHTAGS"),
            "tags": source.get("TAGS"),
            "type": source.get("TYPE"),
            "public_url": source.get("PUBLIC_URL"),
            "date": source.get("DATE")
        })

    aggs = response.get("aggregations", {})
    history_buckets = [
        {
            **bucket,
            "key_as_string": bucket.get("key_as_string"),
            "doc_count": bucket.get("doc_count"),
            "sub_buckets": {
                k: v.get("buckets") if isinstance(v, dict) and "buckets" in v else v
                for k, v in bucket.items() if k not in ("key", "key_as_string", "doc_count")
            }
        }
        for bucket in aggs.get("history", {}).get("buckets", [])
    ]
    sentiment = aggs.get("sentiment", {}).get("buckets", [])
    sense = aggs.get("sense", {}).get("buckets", [])
    reactions_breakdown = aggs.get("reactionsBreakdown", {}).get("buckets", [])
    hours = aggs.get("hours", {}).get("buckets", [])

    result = {
        "total_hits": response.get("hits", {}).get("total", {}).get("value", 0),
        "hits": hits,
        "aggregations": {
            "history": history_buckets,
            "sentiment": sentiment,
            "sense": sense,
            "reactions": aggs.get("reactions", {}).get("value", 0),
            "comments": aggs.get("comments", {}).get("value", 0),
            "forwards": aggs.get("forwards", {}).get("value", 0),
            "views": aggs.get("views", {}).get("value", 0),
            "followers_sum": total_followers,
            "unique_channels": aggs.get("unique_channels", {}).get("value", 0),
            "reactions_breakdown": reactions_breakdown,
            "hours": hours
        }
    }

    return result


async def get_geographic_report(
    search_text: str, 
    start_date: str, 
    end_date: str, 
    subject_type: str, 
    subject_id: int
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramGeographicReport)

    if search_text != "null":
        query_body = json.loads(template.render(
            start_date=start_date,
            end_date=end_date,
            must=[[search_text]],
            should=[[]],
            must_not=[[]]
        ))
    else:
        filter_dic = {}
        if subject_type == "topic":
            filter_dic = topics
        elif subject_type == "person":
            filter_dic = persons
        elif subject_type == "event":
            filter_dic = events
        elif subject_type == "force":
            filter_dic = forces
        else:
            raise HTTPException(status_code=400, detail="Invalid subject type value")

        query_body = json.loads(template.render(
            start_date=start_date,
            end_date=end_date,
            must=filter_dic[subject_id]["must"],
            should=filter_dic[subject_id]["should"],
            must_not=filter_dic[subject_id]["must_not"]
        ))

    with open('/code/utils/province_city_fa.json', 'r', encoding='utf-8') as f:
        try:
            provinces_fa = json.load(f)
        except json.JSONDecodeError:
            provinces_fa = []

    with open('/code/utils/province_city_en.json', 'r', encoding='utf-8') as f:
        try:
            provinces_en = json.load(f)
        except json.JSONDecodeError:
            provinces_en = []

    key2name = {province_data.get('key'): province_data.get('province') for province_data in provinces_en}

    query_body_message = copy.deepcopy(query_body)
    query_body_message['aggs'] = {
        p['key']: {
            'filter': {
                'bool': {
                    'must': [
                        {
                            'bool': {
                                'should': [
                                    {"match_phrase": {"MESSAGE": field}}
                                    for field in [p['province']] + p['cities']
                                ]
                            }
                        }
                    ]
                }
            }
        }
        for p in provinces_fa
    }

    query_body_url = copy.deepcopy(query_body)
    query_body_url.update({"size": 1000, "_source": ["PUBLIC_URL"]})

    response_message, response_url = await asyncio.gather(
        elastic_handler.client.search(index=INDEX_MESSAGES, body=query_body_message),
        elastic_handler.client.search(index=INDEX_MESSAGES, body=query_body_url)
    )

    counts_message = {k: agg['doc_count'] for k, agg in response_message['aggregations'].items()}
    counts_url = {province['key']: 0 for province in provinces_en}
    try:
        for hit in response_url['hits']['hits']:
            try:
                url = hit["_source"].get("PUBLIC_URL", "")
                for province in provinces_en:
                    if any(field in url for field in [province['key']] + province['cities']):
                        counts_url[province['key']] += 1
                        break
            except Exception as e:
                logger.warning(f"Skipping a problematic URL in URL counting in Geographic Report: '{e}'")
                continue
    except Exception as e:
        logger.error(f"Unexpected error in URL counting in Geographic Report: '{e}'")

    return [
        {
            'city': key2name[k],
            'post': counts_message.get(k, 0),
            'url': counts_url.get(k, 0),
            'total': counts_message.get(k, 0) + counts_url.get(k, 0)
        } for k in key2name
    ]


async def get_aja_channels_analysis(
    start_date: str, 
    end_date: str
):
    
    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}

    url_template = services.jinja_template_generator(path=QueryTypes.TelegramChannelInfoByURL)
    url_payload = json.loads(url_template.render(
        urls=list(channel_urls.keys())
    ))
    url_response = await elastic_handler.client.search(index=INDEX_CHANNELS, body=url_payload)

    peer_map = {}
    total_followers = 0
    for hit in url_response["hits"]["hits"]:
        src = hit["_source"]

        followers_list = src.get("FOLLOWERS")
        followers_count = 0
        if isinstance(followers_list, list) and followers_list:
            last_entry = followers_list[0]
            if isinstance(last_entry.get("FOLLOWERS"), int):
                followers_count = last_entry["FOLLOWERS"]
                total_followers += followers_count

        peer_map[src["PEER_ID"]] = {
            "url": src["URL"],
            "title": src.get("TITLE"),
            "followers": followers_count,
            "tag_force": channel_urls[src["URL"]]["tag"],
            "description": src.get("DESCRIPTION"),
            "img": get_channel_image_url(src["PEER_ID"])
        }

    if not peer_map:
        return {"message": "No channels found for given URLs"}

    stats_template = services.jinja_template_generator(path=QueryTypes.TelegramChannelDetailsByPeerID)
    stats_payload = json.loads(stats_template.render(
        peer_ids=list(peer_map.keys()),
        start_date=start_date,
        end_date=end_date
    ))
    stats_response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=stats_payload)
    
    global_aggs = stats_response.get("aggregations", {}).get("global_stats", {})
    global_stats = {
        "total_channels": len(channel_urls),
        "total_posts": int(global_aggs.get("total_posts", {}).get("value", 0)),
        "total_comments": int(global_aggs.get("total_comments", {}).get("value", 0)),
        "total_reactions": int(global_aggs.get("total_reactions", {}).get("value", 0)),
        "total_views": int(global_aggs.get("total_views", {}).get("value", 0)),
        "total_followers": total_followers
    }

    buckets = stats_response.get("aggregations", {}).get("per_channel", {}).get("buckets", [])
    results = []
    for bucket in buckets:
        peer_id = bucket["key"]
        stats = {
            "total_posts": int(bucket["total_posts"]["value"]),
            "total_comments": int(bucket["total_comments"]["value"]),
            "total_reactions": int(bucket["total_reactions"]["value"]),
            "total_views": int(bucket["total_views"]["value"])
        }
        merged = {
            "peer_id": peer_id,
            "url": peer_map[peer_id]["url"],
            "title": peer_map[peer_id]["title"],
            "followers": peer_map[peer_id]["followers"],
            "tag_force": peer_map[peer_id]["tag_force"],
            "description": peer_map[peer_id]["description"],
            "img": peer_map[peer_id]["img"],
            **stats
        }
        results.append(merged)

    results.sort(key=lambda x: x["followers"], reverse=True)
    
    return {
        "global": global_stats,
        "channels": results
    }


async def get_aja_channels_subs(
    num_recent_months: int
):
    result = []
    for url, records in RAW_SUBSCRIBERS.items():
        return_records = records[-num_recent_months:]
        result.append({
            "channel_url": url,
            "history": return_records
        })

    return result


async def add_new_aja_channel(
    url: str,
    tag: str,
    admin: str,
    city: str
):
    
    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}

    if url in channel_urls:
        raise HTTPException(status_code=400, detail=f"Channel already exists: {url}")
    
    channel_urls[url] = {
        "tag": tag,
        "admin": {
            "1": {
                "name": admin,
                "national_id": "",
                "phone": "",
                "account_email": "",
                "account_phone": "",
                "address": "",
                "isCreator": 0
            }
        },
        "city": city
    }
    
    with open('/code/utils/aja_telegram_channels.json', 'w', encoding='utf-8') as f:
        json.dump(channel_urls, f, ensure_ascii=False, indent=4)
    
    return {
        "message": "Channel added successfully",
        "url": url,
        "tag": tag,
        "admin": admin,
        "city": city
    }


async def delete_aja_channel(
    url: str
):

    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}

    if url not in channel_urls:
        raise HTTPException(status_code=404, detail=f"Channel not found: {url}")

    del channel_urls[url]
    
    with open('/code/utils/aja_telegram_channels.json', 'w', encoding='utf-8') as f:
        json.dump(channel_urls, f, ensure_ascii=False, indent=4)

    return {
        "message": "Channel deleted successfully",
        "url": url
    }


async def get_aja_channels_admins():

    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}

    return {url: data["admin"] for url, data in channel_urls.items()}


async def add_new_admin_aja_channels(
       channel_url: str,
       name: str,
       national_id: str,
       phone: str,
       account_email: str,
       account_phone: str,
       address: str,
       isCreator: int
):
    
    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}

    if channel_url not in channel_urls:
        raise HTTPException(status_code=404, detail=f"Channel not found: {channel_url}")

    if national_id in [admin.get("national_id") for admin in channel_urls[channel_url].get("admin", {}).values()]:
        raise HTTPException(status_code=400, detail=f"Admin with national ID '{national_id}' already exists in channel '{channel_url}'")

    admin_data = {
        "name": name,
        "national_id": national_id,
        "phone": phone,
        "account_email": account_email,
        "account_phone": account_phone,
        "address": address,
        "isCreator": isCreator
    }

    existing_admins = channel_urls[channel_url].get("admin", {})
    new_key = str(max([int(k) for k in existing_admins.keys()]) + 1) if existing_admins else "1"
    channel_urls[channel_url].setdefault("admin", {})[new_key] = admin_data

    with open('/code/utils/aja_telegram_channels.json', 'w', encoding='utf-8') as f:
        json.dump(channel_urls, f, ensure_ascii=False, indent=4)

    return {
        "message": "Admin added successfully", 
        "channel_url": channel_url,
        "admin_id": new_key,
        **admin_data
    }


async def delete_an_admin_aja_channels(
         channel_url: str,
         admin_id: str
):
     
     with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
          try:
                channel_urls = json.load(f)
          except json.JSONDecodeError:
                channel_urls = {}
    
     if channel_url not in channel_urls:
          raise HTTPException(status_code=404, detail=f"Channel not found: {channel_url}")
     
     if admin_id not in channel_urls[channel_url].get("admin", {}):
          raise HTTPException(status_code=404, detail=f"Admin ID not found: {admin_id}")
    
     del channel_urls[channel_url]["admin"][admin_id]
    
     with open('/code/utils/aja_telegram_channels.json', 'w', encoding='utf-8') as f:
          json.dump(channel_urls, f, ensure_ascii=False, indent=4)
    
     return {
          "message": "Admin deleted successfully", 
          "channel_url": channel_url,
          "admin_id": admin_id
     }
        

async def get_c2_system_analysis(
    start_date: str, 
    end_date: str
):

    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}
            
    url_template = services.jinja_template_generator(path=QueryTypes.TelegramChannelInfoByURL)
    url_payload = json.loads(url_template.render(
        urls=list(channel_urls.keys())
    ))
    url_response = await elastic_handler.client.search(index=INDEX_CHANNELS, body=url_payload)

    force_keys = ["نیروی زمینی", "نیروی هوایی", "نیروی دریایی", "نیروی پدافند", "عقیدتی سیاسی", "آجا"]
    forces_type_tel = {k: {"followers": 0, "num_channels": 0} for k in force_keys}
    forces_type_eitaa = {k: {"followers": 0, "num_channels": 0} for k in force_keys}

    peer_map = {}
    total_followers = 0
    for hit in url_response["hits"]["hits"]:
        src = hit["_source"]
        force = channel_urls[src["URL"]]["tag"]

        followers_list = src.get("FOLLOWERS")
        followers_count = 0
        if isinstance(followers_list, list) and followers_list:

            followers_records = []
            for f in followers_list:
                if isinstance(f["FETCH_TIME"], str):
                    fetch_date = f["FETCH_TIME"][:10]
                    if start_date <= fetch_date <= end_date:
                        followers_records.append(f["FOLLOWERS"])

            if followers_records:
                followers_count = round(sum(followers_records) / len(followers_records))
            else:
                followers_count = followers_list[0]["FOLLOWERS"]
            total_followers += followers_count

        peer_map[src["PEER_ID"]] = {
            "url": src["URL"],
            "title": src.get("TITLE"),
            "followers": followers_count,
            "admin": channel_urls[src["URL"]]["admin"]["1"]["name"],
            "tag_force": force,
            "description": src.get("DESCRIPTION"),
            "img": get_channel_image_url(src["PEER_ID"])
        }
        forces_type_tel[force]["followers"] += followers_count
        forces_type_tel[force]["num_channels"] += 1

    if not peer_map:
        raise HTTPException(status_code=404, detail="No channels found for given URLs")

    stats_template = services.jinja_template_generator(path=QueryTypes.TelegramChannelDetailsByPeerID)
    stats_payload = json.loads(stats_template.render(
        peer_ids=list(peer_map.keys()),
        start_date=start_date,
        end_date=end_date
    ))
    stats_response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=stats_payload)

    with open('/code/utils/aja_eitaa_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls_eitaa = json.load(f)
        except json.JSONDecodeError:
            channel_urls_eitaa = {}
    
    total_subs_eitaa = 0
    for _, info in channel_urls_eitaa.items():
        subs_count = info["subscribers"]
        force_tag = info["tag"]

        total_subs_eitaa += subs_count
        forces_type_eitaa[force_tag]["followers"] += subs_count
        forces_type_eitaa[force_tag]["num_channels"] += 1
    
    global_aggs = stats_response.get("aggregations", {}).get("global_stats", {})
    global_stats = {
        "total_channels_telegram": len(channel_urls),
        "total_channels_eitaa": len(channel_urls_eitaa),
        "total_followers_telegram": total_followers,
        "total_followers_eitaa": total_subs_eitaa,
        "total_posts": int(global_aggs.get("total_posts", {}).get("value", 0)),
        "total_comments": int(global_aggs.get("total_comments", {}).get("value", 0)),
        "total_reactions": int(global_aggs.get("total_reactions", {}).get("value", 0)),
        "total_views": int(global_aggs.get("total_views", {}).get("value", 0)),
        "each_force_details_telegram": forces_type_tel,
        "each_force_details_eitaa": forces_type_eitaa
    }

    buckets = stats_response.get("aggregations", {}).get("per_channel", {}).get("buckets", [])
    results = []
    for bucket in buckets:
        peer_id = bucket["key"]
        posts = int(bucket["total_posts"]["value"])
        views = int(bucket["total_views"]["value"])
        stats = {
            "posts": posts,
            "comments": int(bucket["total_comments"]["value"]),
            "reactions": int(bucket["total_reactions"]["value"]),
            "views": views,
            "view_sub_ratio": round(((views / posts) / peer_map[peer_id]["followers"]) * 100, 2) if peer_map[peer_id]["followers"] > 0 else 0
        }
        merged = {
            "peer_id": peer_id,
            "url": peer_map[peer_id]["url"],
            "title": peer_map[peer_id]["title"],
            "followers": peer_map[peer_id]["followers"],
            "admin": peer_map[peer_id]["admin"],
            "tag_force": peer_map[peer_id]["tag_force"],
            "description": peer_map[peer_id]["description"],
            "img": peer_map[peer_id]["img"],
            **stats
        }
        results.append(merged)

    results.sort(key=lambda x: x["posts"], reverse=True)
    
    return {
        "global": global_stats,
        "channels": results
    }


async def get_c2_system_messages(
    start_date: str,
    end_date: str,
    size: int,
    page: int
):
    
    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}

    template = services.jinja_template_generator(path=QueryTypes.TelegramAjaChannelsMessages)
    payload = json.loads(template.render(
        urls=list(channel_urls.keys()),
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=(page-1)*size
    ))

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    top_posts = [message['_source'] for message in response['hits']['hits']]
    all_peer_ids = [post['PEER_ID'] for post in top_posts]
    channel_info = await get_channels_overview(list(all_peer_ids))

    for post in top_posts:
        date_val = post.get('DATE')
        dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
        post['DAY'] = dt.strftime("%Y-%m-%d")
        post['HOUR'] = dt.strftime("%H:%M")
        channel_data = channel_info.get(str(post['PEER_ID']), channel_info.get(post['PEER_ID']))
        if channel_data is not None:
            post['CHANNEL_URL'] = channel_data.get('URL', None)
            post['CHANNEL_USERNAME'] = channel_data.get('USERNAME', None)
            post['CHANNEL_FOLLOWERS'] = channel_data.get('FOLLOWERS')[-1]['FOLLOWERS'] if channel_data.get('FOLLOWERS') else 0
            post['CHANNEL_TAG_FORCE'] = channel_urls[post['CHANNEL_URL']]["tag"]
            post['CHANNEL_IMG'] = get_channel_image_url(post['PEER_ID'])

            if post['CHANNEL_FOLLOWERS']:
                view_subs_compare = (post.get('VIEWS_COUNT', 0) / post['CHANNEL_FOLLOWERS']) * 100
                post['VIEW_SUBS_COMPARE'] = round(view_subs_compare, 2)
            else:
                post['VIEW_SUBS_COMPARE'] = 0

    return {
        'doc_count': response['hits']['total']['value'],
        'history': response['aggregations']['history']['buckets'],
        'sentimentBreakdown': {
            sense["key"]: sense["doc_count"]
            for sense in response['aggregations']['sentiment']['buckets']
        },
        'senseBreakdown': {
            sense["key"]: sense["doc_count"]
            for sense in response['aggregations']['sense']['buckets']
        },
        'reactionsBreakdown': {
            r.get("key"): r.get("doc_count", 0)
            for r in response.get('aggregations', {})
                     .get('reactionsBreakdown', {})
                     .get('buckets', [])
        },
        'mediaBreakdown': {
            m["key"]: m["doc_count"]
            for m in response['aggregations']['media_types']['buckets']
        },
        'hoursBreakdown': {
            hour["key"]: hour["doc_count"]
            for hour in response['aggregations']['hours']['buckets']
        },
        'stats': {
            'reactions': response['aggregations']['reactions']['value'],
            'comments':  response['aggregations']['comments']['value'],
            'forwards':  response['aggregations']['forwards']['value'],
            'views':     response['aggregations']['views']['value'],
        },
        'top_posts': top_posts
    }


async def get_c2_system_geographic():

    city_data = defaultdict(lambda: {"count": 0, "tags": defaultdict(int)})

    for path in (
        '/code/utils/aja_telegram_channels.json',
        '/code/utils/aja_eitaa_channels.json'
    ):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except json.JSONDecodeError:
            dataset = {}

        for info in dataset.values():
            cities = info.get("city")
            tag = info.get("tag")
            if cities and tag:
                for c in cities:
                    city_data[c]["count"] += 1
                    city_data[c]["tags"][tag] += 1

    return [
        {
            "city": city,
            "count": data["count"],
            "tags": [{"tag": tag, "count": count} for tag, count in data["tags"].items()]
        }
        for city, data in city_data.items()
    ]


async def get_c2_system_subscribers_growth(
    start_date: str,
    end_date: str
):
    
    with open('/code/utils/aja_telegram_channels.json', 'r', encoding='utf-8') as f:
        try:
            channel_urls = json.load(f)
        except json.JSONDecodeError:
            channel_urls = {}

    template = services.jinja_template_generator(path=QueryTypes.TelegramAjaSubsGrowth)
    payload = json.loads(template.render(
        urls=list(channel_urls.keys())
    ))

    response = await elastic_handler.client.search(index=INDEX_CHANNELS, body=payload)

    results = defaultdict(list)
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        for f in src.get("FOLLOWERS", []):
            fetch_date = f["FETCH_TIME"][:10]
            if start_date <= fetch_date <= end_date:
                results[src["URL"]].append({
                    "FETCH_TIME": fetch_date,
                    "FOLLOWERS": f["FOLLOWERS"]
                })

    return results


async def get_query_by_aggs(
    subject_type: str,
    search_id: int,
    message_type: str, 
    start_date: str, 
    end_date: str
):
    filter_dic = {}
    if subject_type == "topic":
        filter_dic = topics
    elif subject_type == "person":
        filter_dic = persons
    elif subject_type == "event":
        filter_dic = events
    elif subject_type == "force":
        filter_dic = forces
    else:
        raise HTTPException(status_code=400, detail="Invalid subject type value")
    
    template = services.jinja_template_generator(path=QueryTypes.TelegramQueryByAggs)
    payload = json.loads(template.render(
        start_date=start_date,
        end_date=end_date,
        must=filter_dic[search_id]["must"],
        should=filter_dic[search_id]["should"],
        must_not=filter_dic[search_id]["must_not"]
    ))
    
    if message_type == "CHANNELPOST":
        payload["query"]["bool"]["filter"].append({
            "match_phrase": {
                "TYPE": "CHANNELPOST"
            }
        })
    elif message_type == "CHANNELCOMMENT":
        payload["query"]["bool"]["filter"].append({
            "bool": {
                "must_not": [
                    {"match_phrase": {"TYPE": "CHANNELPOST"}}
                ]
            }
        })
    else:
        raise HTTPException(status_code=400, detail="Invalid message type value")

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    
    return {
        'doc_count': response['hits']['total']['value'],
        'history': response['aggregations']['history']['buckets'],
        'sentimentBreakdown': {sense["key"]: sense["doc_count"] for sense in response['aggregations']['sentiment']['buckets']},
        'senseBreakdown': {sense["key"]: sense["doc_count"] for sense in response['aggregations']['sense']['buckets']},
        'reactionsBreakdown': {r.get("key"): r.get("doc_count", 0) for r in response.get('aggregations', {}).get('reactionsBreakdown', {}).get('buckets', [])},
        'hoursBreakdown': {hour["key"]: hour["doc_count"] for hour in response['aggregations']['hours']['buckets']},
        'stats': {
            'reactions': response['aggregations']['reactions']['value'],
            'comments': response['aggregations']['comments']['value'],
            'forwards': response['aggregations']['forwards']['value'],
            'views': response['aggregations']['views']['value'],
        },
        'unique_channels_count': response['aggregations']['unique_channels']['value']
    }


async def get_query_by_msg(
    subject_type: str,
    search_id: int,
    message_type: str,
    start_date: str, 
    end_date: str, 
    size: int, 
    page: int,
    sort: str
):
    filter_dic = {}
    if subject_type == "topic":
        filter_dic = topics
    elif subject_type == "person":
        filter_dic = persons
    elif subject_type == "event":
        filter_dic = events
    elif subject_type == "force":
        filter_dic = forces
    else:
        raise HTTPException(status_code=400, detail="Invalid subject type value")
    
    template = services.jinja_template_generator(path=QueryTypes.TelegramQueryByMessages)
    payload = json.loads(template.render(
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=(page-1)*size,
        must=filter_dic[search_id]["must"],
        should=filter_dic[search_id]["should"],
        must_not=filter_dic[search_id]["must_not"]
    ))

    if message_type == "CHANNELPOST":
        payload["query"]["bool"]["filter"].append({
            "match_phrase": {
                "TYPE": "CHANNELPOST"
            }
        })
    elif message_type == "CHANNELCOMMENT":
        payload["query"]["bool"]["filter"].append({
            "bool": {
                "must_not": [
                    {"match_phrase": {"TYPE": "CHANNELPOST"}}
                ]
            }
        })
    else:
        raise HTTPException(status_code=400, detail="Invalid message type value")

    if sort == "DATE":
        payload['sort'] = [
            {"DATE": {"order": "desc"}}
        ]
    elif sort == "VIEWS":
        payload['sort'] = [
            {"VIEWS_COUNT": {"order": "desc"}}
        ]
    else:
        raise HTTPException(status_code=400, detail="Invalid sort type value")
    
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    top_posts = [message['_source'] for message in response['hits']['hits']]
    all_peer_ids = [post['PEER_ID'] for post in top_posts]
    channel_info = await get_channels_overview(list(all_peer_ids))

    results = []
    for post in top_posts:
        date_val = post.get('DATE')
        dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
        date_val = dt.strftime("%Y-%m-%d")
        time_val = dt.strftime("%H:%M")

        channel_data = channel_info.get(str(post['PEER_ID']), channel_info.get(post['PEER_ID']))

        results.append({
            "MESSAGE": post.get("MESSAGE"),
            "DATE": date_val,
            "TIME": time_val,
            "PUBLIC_URL": post.get("PUBLIC_URL"),
            "MESSAGE_ID": post.get("MESSAGE_ID"),
            "CHANNEL_USERNAME": channel_data.get("USERNAME") if channel_data else None,
            "CHANNEL_IMG": channel_data.get("IMG") if channel_data else None,
            "MEDIA": post.get("MEDIA"),
            "SENTIMENT": post.get("SENTIMENT"),
            "SENCE": post.get("SENCE"),
            "TAGS": post.get("TAGS"),
            "FORWARDS_COUNT": post.get("FORWARDS_COUNT"),
            "VIEWS_COUNT": post.get("VIEWS_COUNT"),
            "REPLIES_COUNT": post.get("REPLIES_COUNT"),
            "REACTIONS_COUNT": post.get("REACTIONS_COUNT"),
            "REACTIONS": post.get("REACTIONS")
        })

    return {
        "top_posts": results
    }