import httpx
import requests
from typing import Dict
import fastapi

BASE_URL = "http://192.168.10.52:9000"

SUMMARIZER_MODEL = f"{BASE_URL}/summary"
GENERATE_TITLE_MODEL = f"{BASE_URL}/title"
TAG_DETECTOR_MODEL = f"{BASE_URL}/tag"
CATEGORY_DETECTOR_MODEL = f"{BASE_URL}/category"
SENSE_DETECTOR_MODEL = f"{BASE_URL}/sense"
SENTIMENT_DETECTOR_MODEL = f"{BASE_URL}/sentiment"
DISTINCT_TAGS_ARMY_DETECTOR_MODEL = f"{BASE_URL}/distinct_tags/army"


def get_summary(message: str) -> Dict:
    resp = requests.post(SUMMARIZER_MODEL, json={'message': message}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def get_title(message: str) -> Dict:
    resp = requests.post(GENERATE_TITLE_MODEL, json={'message': message}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def get_tag(message: str) -> Dict:
    resp = requests.post(TAG_DETECTOR_MODEL, json={'message': message}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def get_category(message: str) -> Dict:
    resp = requests.post(CATEGORY_DETECTOR_MODEL, json={'message': message}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def get_sense(message: str) -> Dict:
    resp = requests.post(SENSE_DETECTOR_MODEL, json={'message': message}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_sentiment(message: str) -> Dict:
    resp = requests.post(SENTIMENT_DETECTOR_MODEL, json={'message': message}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_disticnt_tag_army(message: str) -> Dict:
    resp = requests.post(DISTINCT_TAGS_ARMY_DETECTOR_MODEL, json={'message': message}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
