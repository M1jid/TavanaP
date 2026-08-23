import requests
from typing import Any, Dict, Optional, List
from config import BASE_URL

def get_telegram_channels() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/telegram/channels", timeout=30.0)
    data = resp.json()
    return [item for item in data if not item['blocked'] and not item['in_progress'] and item['subscribed_by'] is None]

def update_telegram_channel(channel_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/channels/{channel_id}", json=data, timeout=30.0)
    return resp.json()

def create_telegram_channel(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/channels", json=[data], timeout=30.0)
    if resp.status_code != 200:
        return resp.text
    return resp.json()

def create_telegram_account(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/accounts", json=[data], timeout=30.0)
    if resp.status_code != 200:
        return resp.text
    return resp.json()

def get_telegram_channel_by_key(key) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/channels_by_key/{key}", timeout=30.0)
    if resp.status_code != 200:
        return resp.text
    return resp.json()
