import logging
import json
from datetime import datetime, date, timedelta
from fastapi import HTTPException

from app.startup import elastic_handler
from queries.queries import QueryTypes
from services import services
from app.startup import minio_handler
from app.startup import elastic_handler

from keywords.filter_forces import forces
from keywords.filter_topics import topics
from keywords.filter_persons import persons
from keywords.filter_events import events

logger = logging.getLogger(__name__)

VALID_SORTS = ["LIKES", "COMMENTS", "DATE", "VIEWS"]

BUCKET_NAME = "instagram-images-posts"
# --- تابع اصلی کوئری اینستاگرام ---
from datetime import date, timedelta, datetime
from fastapi import HTTPException
import json

VALID_SORTS = ["DATE", "LIKES", "COMMENTS", "VIEWS"]
def get_channel_image_url(username,post_id) -> str:
    return minio_handler.generate_presigned_url(bucket_name=BUCKET_NAME, object_name = f"{username}-{post_id}.jpg")


# --- تابع اصلی کوئری اینستاگرام ---
from datetime import date, timedelta, datetime
from fastapi import HTTPException
import json

VALID_SORTS = ["DATE", "LIKES", "COMMENTS", "VIEWS"]

async def _execute_instagram_query(
    template_path,
    filters_dict,
    start_date=None,
    end_date=None,
    size=10,
    page=1,
    sort="LIKES"
):
    # مقداردهی پیش‌فرض تاریخ
    if start_date is None:
        start_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    if end_date is None:
        end_date = date.today().strftime("%Y-%m-%d")

    # ساخت payload از template
    template = services.jinja_template_generator(path=template_path)
    payload = json.loads(template.render(
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=(page - 1) * size,
        must=filters_dict.get("must", []),
        should=filters_dict.get("should", []),
        must_not=filters_dict.get("must_not", [])
    ))

    # بررسی sort
    if sort not in VALID_SORTS:
        raise HTTPException(status_code=400, detail=f"Invalid sort value: {sort}")

    sort_mapping = {
        "DATE": "post.taken_at",
        "LIKES": "post.like_count",
        "COMMENTS": "post.comment_count",
        "VIEWS": "post.views_count"
    }
    payload["sort"] = [{sort_mapping[sort]: {"order": "desc"}}]

    # اجرای query روی ES
    response = await elastic_handler.client.search(index="instagram_post_v4", body=payload)

    top_posts = []
    for hit in response["hits"]["hits"]:
        post = hit.get("_source", {})

        # parse تاریخ
        date_val = post.get("post", {}).get("taken_at")
        if date_val:
            try:
                dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                day = dt.strftime("%Y-%m-%d")
                hour = dt.strftime("%H:%M")
                date_iso = dt.isoformat()
            except Exception:
                day = hour = date_iso = None
        else:
            day = hour = date_iso = None

        # استخراج داده‌ها
        username = post.get("owner", {}).get("username", "")
        caption = post.get("post", {}).get("caption") or ""
        like_count = post.get("post", {}).get("like_count", 0)
        comments_count = post.get("post", {}).get("comment_count", 0)
        views_count = post.get("post", {}).get("views_count", 0)
        hashtags = post.get("post", {}).get("hashtags") or []
        mentions = post.get("post", {}).get("mentions") or []
        location = post.get("post", {}).get("location") or ""
        post_id = post.get("post", {}).get("id", "")
        img = get_channel_image_url(username= username, post_id= post_id)
        raw_url = post.get("post", {}).get("url", "")
        if "| " in raw_url:
            url = raw_url.split("|", 1)[1].strip()
        else:
            url = raw_url.strip() or f"https://www.instagram.com/p/{post_id}/"


        sentiment = post.get("analysis", {}).get("SENTIMENT", "")
        sense = post.get("analysis", {}).get("SENSE")
        if not sense:
            sense_list = []
        elif isinstance(sense, str):
            sense_list = [sense]
        elif isinstance(sense, list):
            sense_list = sense
        else:
            sense_list = []

        tags_analysis = post.get("analysis", {}).get("TAGS") or []

        top_posts.append({
            "username": username,
            "caption": caption,
            "DATE": date_iso,
            "day": day,
            "hour": hour,
            "SENSE": sense_list,
            "sentiment": sentiment,
            "post_id": post_id,
            "shortcode": post_id,
            "url": url,
            "TAGS": tags_analysis,
            "like_count": like_count,
            "comments_count": comments_count,
            "comments": post.get("comments", []) or [],
            "img": img,
            "hashtags": hashtags,
            "mentions": mentions,
            "location": location,
            "views_count": views_count,
            "owner_id": post.get("owner", {}).get("owner_id"),
            "owner_profile_pic": post.get("owner", {}).get("owner_profile_pic_url")
        })

    # پردازش aggregations
    agg = response.get("aggregations", {})

    def parse_buckets(bucket_list):
        return {b["key"]: b.get("doc_count", 0) for b in bucket_list}

    return {
        "took": response.get("took", 0),
        "timed_out": response.get("timed_out", False),
        "_shards": response.get("_shards", {}),
        "hits": response.get("hits", {}),
        "doc_count": response.get("hits", {}).get("total", {}).get("value", 0),
        "history": agg.get("history", {}).get("buckets", []),
        "sentimentBreakdown": parse_buckets(agg.get("sentiment", {}).get("buckets", [])),
        "senseBreakdown": parse_buckets(agg.get("sense", {}).get("buckets", [])),
        "hoursBreakdown": parse_buckets(agg.get("hours", {}).get("buckets", [])),
        "hashtagsBreakdown": parse_buckets(agg.get("hashtags", {}).get("buckets", [])),
        "mentionsBreakdown": parse_buckets(agg.get("mentions", {}).get("buckets", [])),
        "locationsBreakdown": parse_buckets(agg.get("locations", {}).get("buckets", [])),
        "stats": {
            "likes": agg.get("likes", {}).get("value", 0),
            "comments": agg.get("comments", {}).get("value", 0),
            "views": agg.get("views", {}).get("value", 0),
        },
        "publishers": agg.get("unique_accounts", {}).get("value", 0),
        "top_posts": top_posts
    }


# ------------------- APIهای آماده -------------------
async def get_instagram_query_by_topic(search_id: int, start_date=None, end_date=None, size=10, page=1, sort="LIKES"):
    return await _execute_instagram_query(
        template_path=QueryTypes.InstagramFilters,
        filters_dict=topics[search_id],
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=page,
        sort=sort
    )

async def get_insta_query_by_person(search_id: int, start_date=None, end_date=None, size=10, page=1, sort="LIKES"):
    return await _execute_instagram_query(
        template_path=QueryTypes.InstagramFilters,
        filters_dict=persons[search_id],
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=page,
        sort=sort
    )

async def get_insta_query_by_event(search_id: int, start_date=None, end_date=None, size=10, page=1, sort="LIKES"):
    return await _execute_instagram_query(
        template_path=QueryTypes.InstagramFilters,
        filters_dict=events[search_id],
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=page,
        sort=sort
    )

async def get_insta_query_by_force(search_id: int, start_date=None, end_date=None, size=10, page=1, sort="LIKES"):
    return await _execute_instagram_query(
        template_path=QueryTypes.InstagramFilters,
        filters_dict=forces[search_id],
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=page,
        sort=sort
    )


