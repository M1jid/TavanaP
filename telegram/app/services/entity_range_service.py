"""
Message Range Service

This service handles all Elasticsearch queries related to determining
message ranges for fetching from Telegram.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from app.startup import elastic_handler, logger


async def get_update_range(peer_id: int) -> int:
    payload = {
        "size": 1,
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": [
                    {
                        "match_phrase": {
                            "PEER_ID": peer_id
                        }
                    }
                ],
                "filter": [
                    {
                        "range": {
                            "DATE": {
                                "gte": "now-30d/d",
                                "lte": "now-6h/h"
                            }
                        }
                    }
                ]
            }
        },
        "sort": [
            {"MESSAGE_ID": {"order": "desc"}}
        ],
    }
    response = await elastic_handler.client.search(index='telegram-messages', body=payload)
    hits = response['hits']['hits']
    if not hits:
        return None
    last_message_id = int(hits[0]['MESSAGE_ID'])
    last_message_date = hits[0]['MESSAGE_DATE']

    payload = {
        "size": 1,
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"PEER_ID": peer_id}},
                    {
                        "range": {
                            "DATE": {
                                "gte": "now-30d/d",
                                "lte":  last_message_date
                            }
                        }
                    },
                    {
                        "script": {
                            "script": {
                                "source": """
                                    def dateStr = doc['DATE'].value.toString();
                                    if (dateStr.length() == 17 && dateStr.endsWith('Z')) {
                                        dateStr = dateStr.replace('Z', ':00Z');
                                    }
                                    def dateIso = Instant.parse(dateStr);
                                    def fetchTime = Instant.ofEpochSecond(doc['FETCH_TIME'].value);
                                    long diff = ChronoUnit.HOURS.between(dateIso, fetchTime);
                                    return diff < 6;
                                """,
                                "lang": "painless"
                            }
                        }
                    }
                ]
            }
        },
        "sort": [
            {"MESSAGE_ID": {"order": "asc"}}
        ]
    }

    response = await elastic_handler.client.search(index='telegram-messages', body=payload)
    hits = response['hits']['hits']
    if not hits:
        return None
    start_message_id = int(hits[0]['MESSAGE_ID'])
    return start_message_id

async def get_chat_last_message_id(user_id: int, end_message_id: int) -> Optional[int]:
    """Get the last message ID for a specific user chat."""
    payload = {
        "size": 0,
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": [
                    {
                        "match_phrase": {
                            "USER_ID": user_id
                        }
                    }
                ]
            }
        },
        "aggs": {
            "last_index": {"max": {"field": "MESSAGE_ID"}}
        }
    }
    response = await elastic_handler.client.search(index='telegram-chat-messages', body=payload)
    last_index_agg = response['aggregations']['last_index']
    return int(last_index_agg['value']) if last_index_agg['value'] is not None else end_message_id
