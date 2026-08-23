BUCKET_NAME = 'instagram-images-channels'
INSTAGRAM_INDEX_MESSAGES = 'instagram_post_v4'

from app.startup import elastic_handler
from queries.queries import QueryTypes
from services import services
import json
from utils.minio_handler import MinIOHandler
from utils.minio_config import get_minio_config

minio_handler = MinIOHandler(**get_minio_config(type='channel'))


async def instagram_top_trend(start_date: str, end_date: str, size: int = 10):
    template = services.jinja_template_generator(QueryTypes.InstagramTopTrend)
    payload = json.loads(template.render(start_date=start_date, end_date=end_date, size=size))

    response = await elastic_handler.client.search(index=INSTAGRAM_INDEX_MESSAGES, body=payload)
    hits = response.get("hits", {}).get("hits", [])
    aggs = response.get("aggregations", {})

    top_posts = [
        {
            "username": h["_source"].get("username", "N/A"),
            "caption": h["_source"].get("caption", ""),
            "like_count": h["_source"].get("like_count", 0),
            "SENTIMENT": h["_source"].get("SENTIMENT", "N/A"),
            "POST_URL": h["_source"].get("url", "N/A"),
            "TAGS": h["_source"].get("TAGS", []),
            "SENSE": h["_source"].get("SENSE", [])
        }
        for h in hits
    ]

    def parse_buckets(key):
        return {b["key"]: b["doc_count"] for b in aggs.get(key, {}).get("buckets", [])}

    return {
        "top_posts": top_posts,
        "sentimentBreakdown": parse_buckets("sentimentBreakdown"),
        "senseBreakdown": parse_buckets("senseBreakdown"),
        "tagsBreakdown": parse_buckets("tagsBreakdown"),
        "stats": {"like_count": aggs.get("totalLikes", {}).get("value", 0)}
    }
