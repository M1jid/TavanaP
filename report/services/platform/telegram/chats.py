import json
import base64
from site import USER_BASE
from fastapi import HTTPException, status
from app.startup import elastic_handler, kafka_producer, minio_handler

from app.config import (
    MINIO_TELEGRAM_MEDIA_CHATS_BUCKET_NAME as MEDIA_CHATS_BUCKET_NAME,
    TELEGRAM_INDEX_CHAT_MESSAGES as INDEX_CHAT_MESSAGES,
    TELEGRAM_CHATS_MESSAGE_SEND_TOPIC as CHATS_MESSAGE_SEND_TOPIC,
    TELEGRAM_INDEX_USERS as INDEX_USERS,
) 

from queries.queries import QueryTypes
from services import services
from utils import db_handler as db
from services.platform.telegram import users as users_service

from logging import getLogger
logger = getLogger(__name__)


async def get_chat_media_url(file_path: str) -> str:
    return minio_handler.generate_presigned_url(bucket_name=MEDIA_CHATS_BUCKET_NAME, object_name=f'{file_path}')


async def get_active_admins():
    accounts = db.get_telegram_accounts()
    active_accounts = [account for account in accounts if 'admin_listener' in account['roles']]
    result = []
    for account in active_accounts:
        phone = account['phone']
        payload = {
            "size": 1,
            "query": {
                "match_phrase": {"PHONE": phone}
            }
        }
        logger.info(f'Payload: {json.dumps(payload, indent=4, ensure_ascii=False)}')
        response = await elastic_handler.client.search(index=INDEX_USERS, body=payload)
        current_account = response['hits']['hits'][0]['_source']
        current_account['IMG'] = users_service.get_user_image_url(current_account['USER_ID'])
        result.append(current_account)
    return {'total': len(active_accounts), 'accounts': result}


async def get_admin_chats_total_messages_count():
    response = await elastic_handler.client.count(index=INDEX_CHAT_MESSAGES)
    return {'total_messages': response['count']}


async def get_admin_chats_total_messages():
    response = await elastic_handler.client.search(
        index=INDEX_CHAT_MESSAGES,
        body={
            "query": {"match_all": {}},
            "size": 10000,   
            "_source": ["MESSAGE"]
        }
    )
    messages = [hit["_source"]["MESSAGE"] for hit in response["hits"]["hits"]]
    return {"messages": messages}


async def get_admin_chats_total_discussions_count():
    payload = {
        "size": 0,
        "aggs": {
            "total_discussions": {
                "cardinality": {
                    "field": "PEER_ID"
                }
            }
        }
    }
    response = await elastic_handler.client.search(index=INDEX_CHAT_MESSAGES, body=payload)
    return {'total_discussions': response['aggregations']['total_discussions']['value']}

async def get_admin_chat_messages(reciver, peer, size, page, reverse):
    template = services.jinja_template_generator(path=QueryTypes.TelegramChatScroll)
    payload = json.loads(template.render(
        size=1000,
        page=(page-1)*size,
        order="asc" if reverse else "desc",
        reciver=reciver,
        peer=peer
    ))
    response = await elastic_handler.client.search(index=INDEX_CHAT_MESSAGES, body=payload)
    messages = [message['_source'] for message in response['hits']['hits']]
    pending_grouped_media = []
    result_messages = []
    for message in messages:
        if message['MEDIA'] and message['GROUPED_ID'] and not message['MESSAGE']:
            media_url = await get_chat_media_url(message['MEDIA'])
            logger.info(f'Media url: {media_url}')
            pending_grouped_media.append(media_url)
        if message['MEDIA'] and message['GROUPED_ID'] and message['MESSAGE']:
            media_url = await get_chat_media_url(message['MEDIA'])
            pending_grouped_media.append(media_url)
            message['MEDIA']=pending_grouped_media
            result_messages.append(message)
            pending_grouped_media = []
        elif message['MEDIA'] and not message['GROUPED_ID']:
            media_url = await get_chat_media_url(message['MEDIA'])
            message['MEDIA'] = [media_url]
            result_messages.append(message)
            pending_grouped_media = []
        else:
            result_messages.append(message)
    return result_messages

async def get_admin_chat_messages_scroll(reciver, peer, size, page, reverse):
    template = services.jinja_template_generator(path=QueryTypes.TelegramChatScroll)
    payload = json.loads(template.render(
        size=1000,
        page=(page-1)*size,
        order="asc" if reverse else "desc",
        reciver=reciver,
        peer=peer
    ))
    response = await elastic_handler.client.search(index=INDEX_CHAT_MESSAGES, body=payload)
    messages = [message['_source'] for message in response['hits']['hits']]
    pending_grouped_media = []
    result_messages = []
    for message in messages:
        if message['MEDIA'] and message['GROUPED_ID'] and not message['MESSAGE']:
            media_url = await get_chat_media_url(message['MEDIA'])
            logger.info(f'Media url: {media_url}')
            pending_grouped_media.append(media_url)
        if message['MEDIA'] and message['GROUPED_ID'] and message['MESSAGE']:
            media_url = await get_chat_media_url(message['MEDIA'])
            pending_grouped_media.append(media_url)
            message['MEDIA']=pending_grouped_media
            result_messages.append(message)
        elif message['MEDIA'] and not message['GROUPED_ID']:
            media_url = await get_chat_media_url(message['MEDIA'])
            message['MEDIA'] = [media_url]
            result_messages.append(message)
            pending_grouped_media = []
    return result_messages

async def get_admin_chat_peers_scroll(size, admin_filter, after_key_peer, after_key_reciver):
    
    template = services.jinja_template_generator(path=QueryTypes.TelegramChatPeersScroll)
    payload = json.loads(template.render(
        size=size
    ))
    if (after_key_peer or after_key_reciver) and (after_key_peer is None or after_key_reciver is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both after_key_peer and after_key_reciver must be provided or none of them")
    
    if admin_filter:
        payload['query'] = {"match_phrase": {"ADMIN_PEER_ID": admin_filter}}

    if after_key_peer and after_key_reciver:
        payload['aggs']['sources']['composite']['after'] = {"peer": after_key_peer, "reciver": after_key_reciver}
    
    response = await elastic_handler.client.search(index=INDEX_CHAT_MESSAGES, body=payload)
    buckets = response['aggregations']['sources']['buckets']
    
    # Get the after_key for next page
    after_key = response['aggregations']['sources'].get('after_key')
    logger.info(f'After key: {after_key}')
    return {
        "entities": buckets,
        "after_key": after_key,
        "has_more": after_key is not None
    }


async def get_geographic_report():

    with open('/code/utils/province_city_fa.json', 'r', encoding='utf-8') as f:
        try:
            provinces_fa = json.load(f)
        except json.JSONDecodeError:
            provinces_fa = []

    key2name = {p.get('key'): p.get('province') for p in provinces_fa}

    query_body = {
        "size": 0,   
        "track_total_hits": True,
        "aggs": {
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
    }
    response = await elastic_handler.client.search(index=INDEX_CHAT_MESSAGES,body=query_body)

    return [
        {'name': key2name.get(k), 'count': agg.get('doc_count', 0)}
        for k, agg in response.get('aggregations', {}).items()
    ]


async def send_message(data, files):
    media_files = []
    if files:
        for file in files:
            # Read the file content
            file_content = await file.read()
            # Reset file pointer for potential future reads
            await file.seek(0)
            
            media_files.append({
                "filename": file.filename,
                "content_type": file.content_type,
                "data": base64.b64encode(file_content).decode('utf-8'),  # Base64 encoded binary data
                "size": len(file_content)
            })
    
    try:
        result = await kafka_producer.produce(
            topic=CHATS_MESSAGE_SEND_TOPIC,
            value={
                "admin_phone": data["phone_number"], 
                "user_id": data["user_id"], 
                "text": data["text"], 
                "reply_to_msg_id": data["reply_to_msg_id"], 
                "media_files": media_files
            },
            key=str(data["user_id"])
        )
        logger.info(f"Message produced: {result}")
        return result
    finally:
        await kafka_producer.close()