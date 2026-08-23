import logging
import json

from fastapi import HTTPException
from datetime import datetime

from services import services
from queries.queries import QueryTypes

from app.startup import elastic_handler
from app.config import RSS_INDEX_MESSAGES as INDEX_MESSAGES

from keywords.filter_forces import forces
from keywords.filter_topics import topics
from keywords.filter_persons import persons
from keywords.filter_events import events

logger = logging.getLogger(__name__)


async def get_aja_website_analysis(
    start_date: str, 
    end_date: str
):
    website_urls = [
        "aja.ir"
    ]
    
    template = services.jinja_template_generator(path=QueryTypes.RSSInfoByURL)
    payload = json.loads(template.render(
        start_date=start_date,
        end_date=end_date,
        urls=website_urls
    ))

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)

    top_posts = []
    for message in response['hits']['hits']:
        src = message['_source']
        post = {
            "TITLE": src.get("TITLE"),
            "SUMMARY": src.get("SUMMARY"),
            "LINK": src.get("LINK"),
            "AUTHOR": src.get("AUTHOR"),
            "CHANNEL_NAME": src.get("CHANNEL_NAME"),
            "IMAGE": src.get("IMAGE"),
            "TAGS": src.get("TAGS"),
            "SENTIMENT": src.get("SENTIMENT")   
        }
        try:
            dt = datetime.fromisoformat(src.get('DATE').replace('Z', '+00:00'))
            post["DATE"] = dt.strftime("%Y-%m-%d")
            post["TIME"] = dt.strftime("%H:%M")
        except Exception as e:
            logger.error(f"Cannot parse the date: {e}")

        top_posts.append(post) 

    return {
        "total": response["hits"]['total']['value'],
        "top_posts": top_posts
    }


async def get_query_by_aggs(
    subject_type: str,
    search_id: int, 
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
    
    template = services.jinja_template_generator(path=QueryTypes.RSSQueryByAggs)
    payload = json.loads(template.render(
        start_date=start_date,
        end_date=end_date,
        must=filter_dic[search_id]["must"],
        should=filter_dic[search_id]["should"],
        must_not=filter_dic[search_id]["must_not"]
    ))

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    
    publishers_dict = {
        pub["key"]: pub["doc_count"]
        for pub in response["aggregations"]["publishers"]["buckets"]
    }
    return {
        "doc_count": response['hits']['total']['value'],
        "history": response['aggregations']['history']['buckets'],
        "sentimentBreakdown": {
            sense["key"]: sense["doc_count"]
            for sense in response["aggregations"]["sentiment"]["buckets"]
        },
        "publishers_count": len(publishers_dict),
        "publishers": publishers_dict,
        "hoursBreakdown": {
            hour["key"]: hour["doc_count"]
            for hour in response["aggregations"]["hours"]["buckets"]
        }
    }


async def get_query_by_msg(
    subject_type: str,
    search_id: int, 
    start_date: str, 
    end_date: str, 
    size: int, 
    page: int
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
    
    template = services.jinja_template_generator(path=QueryTypes.RSSQueryByMessages)
    payload = json.loads(template.render(
        start_date=start_date,
        end_date=end_date,
        size=size,
        page=(page-1)*size,
        must=filter_dic[search_id]["must"],
        should=filter_dic[search_id]["should"],
        must_not=filter_dic[search_id]["must_not"]
    ))

    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload)
    
    top_posts = []
    for message in response['hits']['hits']:
        src = message['_source']
        post = {
            "TITLE": src.get("TITLE"),
            "SUMMARY": src.get("SUMMARY"),
            "LINK": src.get("LINK"),
            "AUTHOR": src.get("AUTHOR"),
            "CHANNEL_NAME": src.get("CHANNEL_NAME"),
            "IMAGE": src.get("IMAGE"),
            "TAGS": src.get("TAGS"),
            "SENTIMENT": src.get("SENTIMENT")  
        }
        try:
            dt = datetime.fromisoformat(src.get('DATE').replace('Z', '+00:00'))
            post["DATE"] = dt.strftime("%Y-%m-%d")
            post["TIME"] = dt.strftime("%H:%M")
        except Exception as e:
            logger.error(f"Cannot parse the date: {e}")
            
        top_posts.append(post)

    return {
        "top_posts": top_posts
    }