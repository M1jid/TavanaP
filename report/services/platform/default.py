import logging
import json

from app.startup import elastic_handler
from app.config import RSS_INDEX_MESSAGES
from app.config import TELEGRAM_INDEX_MESSAGES

from services import services
from queries.queries import QueryTypes


logger = logging.getLogger(__name__)


async def get_daily_received_messages():

    SOURCE_FIELDS = {
        TELEGRAM_INDEX_MESSAGES: "PEER_ID",
        RSS_INDEX_MESSAGES: "CHANNEL_NAME.keyword"
        # INDEX_INSTAGRAM: "account_id.keyword"
    }

    INDEX_LABELS = {
        TELEGRAM_INDEX_MESSAGES: "TELEGRAM_INDEX_MESSAGES",
        RSS_INDEX_MESSAGES: "RSS_INDEX_MESSAGES"
        # INSTAGRAM_INDEX_MESSAGES: "INSTAGRAM_INDEX_MESSAGES",
    }

    template = services.jinja_template_generator(QueryTypes.DefaultDailyReceivedMessages)

    results = {}
    total_messages = 0
    total_unique = 0
    for index, source_field in SOURCE_FIELDS.items():
        logger.info("Index: %s", index)
        payload = json.loads(template.render(
            start_date="now-1d/d",
            end_date="now",
            source_field=source_field
        ))
        resp = await elastic_handler.client.search(index=index, body=payload)

        messages = resp["hits"]["total"]["value"]
        unique_sources = resp["aggregations"]["unique_sources"]["value"]
        label = INDEX_LABELS.get(index, index)
        results[label] = {
            "messages": messages,
            "unique_sources": unique_sources
        }
        total_messages += messages
        total_unique += unique_sources

    results["TOTAL"] = {
        "messages": total_messages,
        "unique_sources": total_unique
    }
    
    return results