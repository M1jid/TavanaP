#!/usr/bin/env python3
import asyncio
import json
import re
from io import BytesIO
from datetime import datetime
import requests
from instaloader import Instaloader, Post

from config import *
from utils import *
from models import *
from minio_handler import MinIOHandler
from minio_config import get_minio_config
from date_time_mapper import get_jalali_date, get_time
from nats.aio.client import Client as NATS

# ----------------------------
# تنظیمات پروکسی
# ----------------------------
PROXIES_REQUESTS = {
    "http": "http://192.168.10.50:10809",
    "https": "http://192.168.10.50:10809",
}

# ----------------------------
# MinIO handler
# ----------------------------
minio_config = get_minio_config(type="channel")
minio_handler = MinIOHandler(**minio_config)

# ----------------------------
# NATS settings
# ----------------------------
NATS_SERVER = "nats://192.168.10.61:4222"
SUBJECT_LAST_POSTS = "instagram.last_posts"
DURABLE_LAST_POSTS = "instagram_last_posts_durable"

# ----------------------------
# Logger
# ----------------------------
def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ----------------------------
# Helpers
# ----------------------------
def clean_caption(caption: str) -> str:
    no_hashtags = re.sub(r"#\S+", "", caption)
    return re.sub(r"\s+", " ", no_hashtags).strip()

def extract_shortcode(url_or_shortcode: str) -> str:
    m = re.search(r"(?:/p/|/tv/|/reel/)([A-Za-z0-9_-]+)", url_or_shortcode)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]+", url_or_shortcode):
        return url_or_shortcode
    raise ValueError("آدرس یا shortcode پست معتبر نیست.")

def download_and_upload_photo(username: str, post_id: str, img_src: str):
    if not img_src or not img_src.startswith("http"):
        return None
    try:
        resp = requests.get(img_src, timeout=60, proxies=PROXIES_REQUESTS)
        resp.raise_for_status()
        file_obj = BytesIO(resp.content)
        object_name = f"{username}-{post_id}.jpg"
        success = minio_handler.upload_fileobj(
            file_obj,
            object_name=object_name,
            bucket_name="instagram-images-posts",
            content_type="image/jpeg",
        )
        if success:
            return minio_handler.generate_presigned_url(
                object_name=object_name,
                bucket_name="instagram-images-posts",
                expiration=86400,
            )
    except Exception as e:
        log(f"❌ Download/Upload failed for {post_id}: {e}")
    return img_src

def timestamp_to_iso(ts):
    try:
        return datetime.utcfromtimestamp(ts).isoformat()
    except Exception:
        return None

# ----------------------------
# پردازش پست اینستاگرام
# ----------------------------
def process_post_instaloader(post_url: str):
    try:
        loader = Instaloader()
        loader.context._session.proxies = PROXIES_REQUESTS
        shortcode = extract_shortcode(post_url)

        post = Post.from_shortcode(loader.context, shortcode)
        raw_node = getattr(post, "_node", {})

        final_photo_url = download_and_upload_photo(post.owner_username, post.shortcode, raw_node.get("display_url"))
        display_resources = raw_node.get("display_resources", [])
        thumbnails = [
            download_and_upload_photo(post.owner_username, f"{post.shortcode}-{i}", res.get("src"))
            for i, res in enumerate(display_resources)
        ]
        owner_profile_pic_url = download_and_upload_photo(
            post.owner_username, "profile-pic", getattr(post.owner_profile, "profile_pic_url", None)
        )

        caption = raw_node.get("title") or post.caption or ""
        caption_cleaned = clean_caption(caption)
        hashtags = re.findall(r"#(\w+)", caption)
        mentions = re.findall(r"@(\w+)", caption)
        views = getattr(post, "video_view_count", None)

        structured_comments = []
        for edge in raw_node.get("edge_media_to_parent_comment", {}).get("edges", []):
            node = edge.get("node", {})
            comment_text = node.get("text")
            username = node.get("owner", {}).get("username")
            comment_created_at = timestamp_to_iso(node.get("created_at"))

            replies = []
            for reply_edge in node.get("edge_threaded_comments", {}).get("edges", []):
                reply_node = reply_edge.get("node", {})
                replies.append({
                    "username": reply_node.get("owner", {}).get("username"),
                    "comment": reply_node.get("text"),
                    "likes": reply_node.get("edge_liked_by", {}).get("count", 0),
                    "created_at": timestamp_to_iso(reply_node.get("created_at")),
                    "profile_pic_url": download_and_upload_photo(
                        reply_node.get("owner", {}).get("username"),
                        "profile-pic",
                        reply_node.get("owner", {}).get("profile_pic_url")
                    )
                })

            structured_comments.append({
                "username": username,
                "comment": comment_text,
                "likes": node.get("edge_liked_by", {}).get("count", 0),
                "created_at": comment_created_at,
                "profile_pic_url": download_and_upload_photo(username, "profile-pic", node.get("owner", {}).get("profile_pic_url")),
                "replies": replies
            })

        post_data = {
            "post": {
                "id": post.shortcode,
                "url": post_url,
                "caption": caption,
                "clean_caption": caption_cleaned,
                "taken_at": post.date_utc.isoformat(),
                "like_count": post.likes,
                "comment_count": post.comments,
                "views": views,
                "is_video": post.is_video,
                "final_photo_url": final_photo_url,
                "thumbnails": thumbnails,
                "hashtags": hashtags,
                "mentions": mentions,
                "location": post.location.name if post.location else None,
            },
            "owner": {
                "username": post.owner_username,
                "owner_id": post.owner_id,
                "profile_pic_url": owner_profile_pic_url,
            },
            "analysis": {
                "SENSE": sense_model(caption),
                "TAGS": category_model(caption),
                "SENTIMENT": sentiment_model(caption),
            },
            "comments": structured_comments,
        }

        print(json.dumps(post_data, indent=2, ensure_ascii=False))
        jdate = get_jalali_date(post.date_utc)
        hour = get_time(post.date_utc)
        telegram_context = (
            f"📍{caption}\n\n"
            f"🔹<b>منبع:</b> {post.owner_username}\n"
            f"🖥<b>آدرس خبر:</b> <a href=\"{post_url}\">لینک مطلب</a>\n"
            f"🗓<b>تاریخ انتشار:</b> {jdate}\n"
            f"⏰<b>ساعت انتشار:</b> {hour}\n"
            f"🗂 <b>بستر:</b> اینستاگرام\n"
            f"🖼 <b>عکس پست:</b> <a href=\"{final_photo_url}\">لینک عکس</a>\n"
        )

        kafka_router.route_message({
            'message': telegram_context,
            'content': caption,
            'resource': 'instagram',
            'parse_mode': 'HTML'
        })

        es.index(index=INDEX_NAME, document=post_data)
        log(f"✅ Post @{post.owner_username} processed successfully")
        return post_data

    except Exception as e:
        log(f"❌ Failed to process post {post_url}: {e}")
        return None

# ----------------------------
# هندل پیام‌های NATS
# ----------------------------
async def handle_message(msg):
    try:
        payload = json.loads(msg.data.decode())
        username = payload.get("username")
        last_post_url = payload.get("last_post")

        log(f"🔔 Received {username} -> {last_post_url}")

        if not last_post_url or last_post_url == "string":
            log(f"⚠️ No valid last post for {username}, skipping.")
            await msg.ack()
            return

        process_post_instaloader(last_post_url)
        await msg.ack()

    except Exception as e:
        log(f"❌ Error processing message: {e}")
        await msg.ack()

# ----------------------------
# Main async
# ----------------------------
async def main():
    nc = NATS()
    await nc.connect(NATS_SERVER)
    log(f"✅ Connected to NATS server at {NATS_SERVER}")

    js = nc.jetstream()
    
    # اطمینان از اینکه استریم وجود دارد
    try:
        await js.add_stream(
            name="INSTAGRAM_LAST_POSTS",
            subjects=[SUBJECT_LAST_POSTS],
            storage="file"
        )
        log("✅ JetStream stream 'INSTAGRAM_LAST_POSTS' created")
    except Exception:
        log("ℹ️ Stream 'INSTAGRAM_LAST_POSTS' already exists or could not be created")

    sub = await js.subscribe(SUBJECT_LAST_POSTS, durable=DURABLE_LAST_POSTS)
    log(f"📡 Subscribed to subject '{SUBJECT_LAST_POSTS}' with durable '{DURABLE_LAST_POSTS}'")

    async for msg in sub.messages:
        await handle_message(msg)

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    asyncio.run(main())
