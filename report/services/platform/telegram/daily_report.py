import json
import logging

from app.config import TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES
from app.config import TELEGRAM_INDEX_CHANNELS as INDEX_CHANNELS
from app.startup import elastic_handler

from services import services
from services.platform.telegram.channels import get_channel_image_url
from queries.queries import QueryTypes
from keywords.filter_daily_popular_posts import filter_daily_popular_posts


logger = logging.getLogger(__name__)


async def get_popular_posts():
    template = services.jinja_template_generator(path=QueryTypes.TelegramDailyPopularPost)
    payload = template.render(
        start_date="now-1d/d",
        end_date="now",
        must=filter_daily_popular_posts["must"],
        should=filter_daily_popular_posts["should"],   
        must_not=filter_daily_popular_posts["must_not"]
    )

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    
    top_posts_hits = (
        response
        .get("aggregations", {})
        .get("top_posts", {})
        .get("hits", {})
        .get("hits", [])
    )

    results = []
    for hit in top_posts_hits:
        src = hit["_source"]
        results.append({
            "message_type": src.get("TYPE", ""),
            "message": src.get("MESSAGE", ""),
            "date": src.get("DATE", ""),
            "views": src.get("VIEWS_COUNT", 0),
            "forwards": src.get("FORWARDS_COUNT", 0),
            "reactions": src.get("REACTIONS_COUNT", 0),
            "replies": src.get("REPLIES_COUNT", 0),
            "public_url": src.get("PUBLIC_URL", "")
        })

    return results


async def get_popular_channels():
    template = services.jinja_template_generator(path=QueryTypes.TelegramDailyPopularChannel)
    payload = template.render(
        start_date="now-1d/d",
        end_date="now"
    )

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    buckets = response.get("aggregations", {}).get("top_channels", {}).get("buckets", [])
    channel_ids = [bucket.get("key") for bucket in buckets]
    channels_info = await get_channels_overview(channel_ids)
    
    results = []
    for bucket in buckets:
        channel_id = bucket.get("key")
        channel_data = channels_info.get(str(channel_id))

        results.append({
            "channel_username": channel_data.get("USERNAME"),
            "channel_url": channel_data.get('URL'),
            "channel_title": channel_data.get('TITLE'),      
            "channel_followers": channel_data["FOLLOWERS"][-1].get("FOLLOWERS", 0),
            "channel_description": channel_data.get('DESCRIPTION'),
            "channel_img": channel_data.get('IMG'),
            "total_forwards": bucket.get("total_forwards", {}).get("value", 0),
            "total_reactions": bucket.get("total_reactions", {}).get("value", 0),
            "total_replies": bucket.get("total_replies", {}).get("value", 0),
            "total_views": bucket.get("total_views", {}).get("value", 0)
        })

    return results


async def get_similar_messages(
    similarity_threshold: int
):
    template = services.jinja_template_generator(path=QueryTypes.TelegramDailySimilarMessage)
    payload = template.render(
        start_date="2025-08-01",
        end_date="2025-08-30",
        exclude_tags=["متفرقه", "ورزشی"] 
    )
    
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    results = []
    for bucket in response.get("aggregations", {}).get("top_tags", {}).get("buckets", []):
        hits = bucket.get("top_post", {}).get("hits", {}).get("hits", [])
        if not hits:
            continue
        top_hit = hits[0]
        top_post = top_hit["_source"]
        top_id = top_hit["_id"]
        top_message = top_post["MESSAGE"]

        similarity_payload = {
            "size": 5,  
            "query": {
                "more_like_this": {
                    "fields": ["MESSAGE"],
                    "like": [
                        {
                            "_id": top_id
                        }
                    ],
                    "min_term_freq": 1,
                    "max_query_terms": 12,
                    "min_doc_freq": 1
                }
            }
        }
        sim_response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=similarity_payload)

        similar_hits = []
        added_peer_ids = []
        for res in sim_response.get("hits", {}).get("hits", []):
            peer_id = res["_source"]["PEER_ID"]

            if peer_id == top_post["PEER_ID"] or peer_id in added_peer_ids:
                continue

            sim_score = round(res["_score"])
            if sim_score >= similarity_threshold:
                similar_hits.append(res)
                added_peer_ids.append(peer_id)
        
        result_item = {
            "topic": bucket["key"],
            "channel1_url": top_post["PUBLIC_URL"].rsplit("/", 1)[0],
            "channel1_username": await extract_username_from_url(top_post["PUBLIC_URL"]),
            "message1": top_message,
            "date_msg1": top_post["DATE"],
            "post1_url": top_post["PUBLIC_URL"],
            "channel1_img": get_channel_image_url(top_post["PEER_ID"])
        }

        for i, hit in enumerate(similar_hits, start=2):
            sim_source = hit["_source"]
            sim_score = min(round(hit["_score"]), 100)
            result_item[f"channel{i}_url"] = sim_source.get("PUBLIC_URL").rsplit("/", 1)[0]
            result_item[f"channel{i}_username"] = await extract_username_from_url(sim_source.get("PUBLIC_URL", ""))
            result_item[f"message{i}"] = sim_source["MESSAGE"]
            result_item[f"date_msg{i}"] = sim_source.get("DATE")
            result_item[f"post{i}_url"] = sim_source.get("PUBLIC_URL")
            result_item[f"channel{i}_img"] = get_channel_image_url(sim_source.get("PEER_ID"))
            result_item[f"similarity{i}"] = f"{sim_score}%"

        results.append(result_item)
        
    return results


# async def get_trending_news_summary():
#     template = services.jinja_template_generator(path=QueryTypes.TelegramDailyTrendingNewsSummary)
#     payload = template.render(
#         start_date="now-1d/d",
#         end_date="now"
#     )

#     response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

#     top_posts_hits = (
#         response
#         .get("aggregations", {})
#         .get("top_posts", {})
#         .get("hits", {})
#         .get("hits", [])
#     )

#     results = []
#     seen_messages = set()
#     for hit in top_posts_hits:
#         message_full = hit.get("_source", {}).get("MESSAGE", "")
#         public_url = hit.get("_source", {}).get("PUBLIC_URL", "")
#         channel_username = await extract_username_from_url(public_url)

#         message_summary = await summarize_text(message_full)
#         BANNED_WORDS = [] 
#         if await contains_banned_word(message_summary, BANNED_WORDS):
#             continue

#         if message_summary not in seen_messages:
#             seen_messages.add(message_summary)
#             results.append({
#                 "channel": channel_username,
#                 "message": message_summary,
#                 "public_url": public_url
#             })

#     return {
#         "count": len(results),
#         "results": results
#     }


# async def get_wordcloud():
#     template = services.jinja_template_generator(path=QueryTypes.TelegramDailyTrendingNewsSummary)
#     payload = template.render(
#         start_date="now-1d/d",
#         end_date="now"
#     )

#     response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

#     top_posts_hits = (
#         response
#         .get("hits", {})
#         .get("hits", [])
#     )

#     messages = [
#         hit.get("_source", {}).get("MESSAGE", "")
#         for hit in top_posts_hits
#     ]

#     full_text = " ".join(messages)
#     words = re.findall(r'\b\w+\b', full_text)
#     word_counts = collections.Counter(words)

#     results = [
#         {"word": word, "count": count}
#         for word, count in word_counts.most_common()
#     ]

#     return {
#         "count": len(results),
#         "results": results
#     }


async def get_most_reaction_channels():
    template = services.jinja_template_generator(path=QueryTypes.TelegramDailyMostReactionChannel)
    payload = json.loads(template.render(
        start_date="now-1d/d",
        end_date="now"
    ))

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    channels = []
    for bucket in response["aggregations"]["channels_by_reactions"]["buckets"]:
        doc = bucket["top_channels"]["hits"]["hits"][0]["_source"]
        peer_id = bucket["key"]
        channels.append({
            "username": await extract_username_from_url(doc.get("PUBLIC_URL")),
            "public_url": doc.get("PUBLIC_URL").rsplit("/", 1)[0],
            "total_reactions": bucket["reactions"]["value"],
            "img": get_channel_image_url(peer_id)
        })

    return channels


async def get_most_comment_channels():
    template = services.jinja_template_generator(path=QueryTypes.TelegramDailyMostCommentChannel)
    payload = json.loads(template.render(
        start_date="now-1d/d",
        end_date="now"
    ))

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    channels = []
    for bucket in response["aggregations"]["channels_by_comments"]["buckets"]:
        doc = bucket["top_channels"]["hits"]["hits"][0]["_source"]
        peer_id = bucket["key"]
        channels.append({
            "username": await extract_username_from_url(doc.get("PUBLIC_URL")),
            "public_url": doc.get("PUBLIC_URL").rsplit("/", 1)[0],
            "total_comments": bucket["comments"]["value"],
            "img": get_channel_image_url(peer_id)
        })

    return channels


async def get_channels_overview(
    channel_ids: list[int]
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


async def extract_username_from_url(url: str) -> str:
    try:
        return url.split("t.me/")[1].split("/")[0]
    except IndexError:
        return ""
    

# async def summarize_text(text: str, max_length: int = 150) -> str:
#     lines = text.split("\n")
#     first_line = lines[0] if len(lines) > 0 else ""
    
#     if len(first_line) < 15 and len(lines) > 1:
#         second_line = lines[1]
#         combined = first_line + " " + second_line
#         if len(combined) > max_length:
#             return combined[:max_length] + "..."
#         else:
#             return combined
#     else:
#         if len(first_line) > max_length:
#             return first_line[:max_length] + "..."
#         else:
#             return first_line


# async def contains_banned_word(text: str, banned_words: list) -> bool:
#     for word in banned_words:
#         pattern = re.compile(re.escape(word), re.IGNORECASE)
#         if pattern.search(text):
#             return True
#     return False