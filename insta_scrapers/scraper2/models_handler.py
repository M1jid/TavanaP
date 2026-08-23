import httpx
import requests
from typing import Dict
import fastapi

import requests
from typing import Dict
import fastapi

# آدرس مدل‌ها
SUMMARIZER_MODEL = "http://192.168.10.52:9000/summary"
GENERATE_TITLE_MODEL = "http://192.168.10.52:9000/title"
TAG_DETECTOR_MODEL = "http://192.168.10.52:9000/tag"
CATEGORY_DETECTOR_MODEL = "http://192.168.10.52:9000/category"
SENSE_DETECTOR_MODEL = "http://192.168.10.52:9000/sense"
SENTIMENT_DETECTOR_MODEL = "http://192.168.10.52:9000/sentiment"
DISTINCT_TAGS_ARMY_DETECTOR_MODEL = "http://192.168.10.52:9000/distinct_tags/army"

def post_without_proxy(url: str, payload: Dict, timeout: float = 30.0) -> Dict:
    session = requests.Session()
    session.trust_env = False   
    try:
        resp = session.post(url, json=payload, timeout=timeout)
        if resp.status_code != 200:
            raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise fastapi.HTTPException(status_code=500, detail=f"Request to {url} failed: {e}")

def get_summary(message: str) -> Dict:
    return post_without_proxy(SUMMARIZER_MODEL, {'message': message})

def get_title(message: str) -> Dict:
    return post_without_proxy(GENERATE_TITLE_MODEL, {'message': message})

def get_tag(message: str) -> Dict:
    return post_without_proxy(TAG_DETECTOR_MODEL, {'message': message})

def get_category(message: str) -> Dict:
    return post_without_proxy(CATEGORY_DETECTOR_MODEL, {'message': message})

def get_sense(message: str) -> Dict:
    return post_without_proxy(SENSE_DETECTOR_MODEL, {'message': message})

def get_sentiment(message: str) -> Dict:
    return post_without_proxy(SENTIMENT_DETECTOR_MODEL, {'message': message})

def get_disticnt_tag_army(message: str) -> Dict:
    return post_without_proxy(DISTINCT_TAGS_ARMY_DETECTOR_MODEL, {'message': message})

