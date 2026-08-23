from app.startup import elastic_handler
from queries.queries import QueryTypes
from services import services
import json
from utils.minio_handler import MinIOHandler
from utils.minio_config import get_minio_config

minio_handler = MinIOHandler(**get_minio_config(type='channel'))


async def get_aja_pages_analysis(start_date: str, end_date: str):
    usernames = [
        "padafandmedia_ir", "daef.emamali", "sarbazi_text",
        "varzesh.aja_ir", "hamsar.arteshi", "nahajamedia_ir",
        "habibsayyari", "dejban_artesh", "ajamedia_ir"
    ]

    username_force_map = {
        "padafandmedia_ir": "نیروی پدافند", "daef.emamali": "نیروی زمینی",
        "sarbazi_text":"نیروی زمینی", "varzesh.aja_ir": "نیروی هوایی",
        "hamsar.arteshi": "عقیدتی سیاسی", "nahajamedia_ir": "نیروی هوایی",
        "habibsayyari": "آجا", "dejban_artesh": "نیروی زمینی",
        "ajamedia_ir": "نیروی دریایی"
    }

    template = services.jinja_template_generator(QueryTypes.InstagramPagePostsByUsername)
    payload = json.loads(template.render(usernames=usernames))
    response = await elastic_handler.client.search(index="instagram_pages_data", body=payload)

    pages = {}
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        username = src["username"]
        pages[username] = {
            "peer_id": username,
            "url": f"https://www.instagram.com/{username}/",
            "title": username,
            "followers": src.get("follower_count", 0),
            "description": src.get("bio_text"),
            "img": MinIOHandler(**get_minio_config(type='channel')).generate_presigned_url(
                object_name=f"{username}.jpg", bucket_name="instagram-images-avatar", expiration=86400
            ),
            "posts": src.get("post_count", 0),
            "comments": 0,
            "reactions": 0,
            "views": 0,
            "tag_force": username_force_map.get(username)
        }

    if not pages:
        return {"message": "No Instagram pages found for given usernames"}

    # جمع‌آوری آمار
    for username, page in pages.items():
        stats_payload = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"username": username}},
                        {"range": {"taken_at": {"gte": start_date, "lte": end_date}}}
                    ]
                }
            },
            "aggs": {
                "total_comments": {"sum": {"field": "comments_count"}},
                "total_reactions": {"sum": {"field": "like_count"}},
                "total_views": {"sum": {"field": "views_count"}}
            }
        }
        stats = await elastic_handler.client.search(index="instagram_post_v4", body=stats_payload)
        aggs = stats.get("aggregations", {})
        page["comments"] = int(aggs.get("total_comments", {}).get("value", 0))
        page["reactions"] = int(aggs.get("total_reactions", {}).get("value", 0))
        page["views"] = int(aggs.get("total_views", {}).get("value", 0))

    results = sorted(pages.values(), key=lambda x: x["followers"], reverse=True)

    force_keys = ["نیروی زمینی", "نیروی هوایی", "نیروی دریایی", "نیروی پدافند", "آجا","عقیدتی سیاسی"]
    force_stats = {k: {"followers": 0, "num_channels": 0} for k in force_keys}
    for ch in results:
        tag = ch.get("tag_force")
        if tag in force_stats:
            force_stats[tag]["followers"] += ch["followers"]
            force_stats[tag]["num_channels"] += 1

    global_stats = {
        "total_channels": len(results),
        "total_posts": sum(p["posts"] for p in results),
        "total_comments": sum(p["comments"] for p in results),
        "total_reactions": sum(p["reactions"] for p in results),
        "total_views": sum(p["views"] for p in results),
        "total_followers": sum(p["followers"] for p in results),
        "each_force_details": force_stats
    }

    return {"global": global_stats, "channels": results}
