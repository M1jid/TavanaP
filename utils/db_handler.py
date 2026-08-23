import requests
from typing import Any, Dict, Optional, List

BASE_URL = "http://192.168.10.60:9000"

import fastapi


# -------------------------- Instagram Pages -------------------------- #

def get_instagram_page_all() -> Dict:
    resp = requests.get(f"{BASE_URL}/instagram/all", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()

def get_instagram_page(id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/instagram/{id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def create_instagram_page(page_data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/instagram", json=page_data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_instagram_page(id: int, page_data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/instagram/{id}", json=page_data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_instagram_page(id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/instagram/{id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

# -------------------------- Telegram Peers  -------------------------- #

def get_telegram_peer(
    id: Optional[int] = None,
    peer_id: Optional[int] = None,
    subscriber: Optional[int] = None,
    username: Optional[str] = None,
    url: Optional[str] = None
) -> Dict:
    params = {}
    if id is not None:
        params['id'] = id
    if peer_id is not None:
        params['peer_id'] = peer_id
    if subscriber is not None:
        params['subscriber'] = subscriber
    if username is not None:
        params['username'] = username
    if url is not None:
        params['url'] = url
    
    resp = requests.get(f"{BASE_URL}/telegram/peers", params=params, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_telegram_peer(
    id: Optional[int] = None,
    peer_id: Optional[int] = None,
    subscriber: Optional[int] = None,
    username: Optional[str] = None,
    url: Optional[str] = None
) -> Dict:
    params = {}
    if id is not None:
        params['id'] = id
    if peer_id is not None:
        params['peer_id'] = peer_id
    if subscriber is not None:
        params['subscriber'] = subscriber
    if username is not None:
        params['username'] = username
    if url is not None:
        params['url'] = url
    
    resp = requests.delete(f"{BASE_URL}/telegram/peers", params=params, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_telegram_peer(
    peer_data: Dict[str, Any],
    id: Optional[int] = None,
    peer_id: Optional[int] = None,
    username: Optional[str] = None,
    url: Optional[str] = None
) -> Dict:
    params = {}
    if id is not None:
        params['id'] = id
    elif peer_id is not None:
        params['peer_id'] = peer_id
    elif username is not None:
        params['username'] = username
    elif url is not None:
        params['url'] = url
    else:
        return None
    resp = requests.put(f"{BASE_URL}/telegram/peers", json=peer_data, params=params, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def block_telegram_peer(
    id: Optional[int] = None,
    peer_id: Optional[int] = None,
    username: Optional[str] = None,
    url: Optional[str] = None
) -> Dict:
    params = {}
    if id is not None:
        params['id'] = id
    if peer_id is not None:
        params['peer_id'] = peer_id
    if username is not None:
        params['username'] = username
    if url is not None:
        params['url'] = url
    
    resp = requests.put(f"{BASE_URL}/telegram/peers/block", params=params, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def unblock_telegram_peer(
    id: Optional[int] = None,
    peer_id: Optional[int] = None,
    username: Optional[str] = None,
    url: Optional[str] = None
) -> Dict:
    params = {}
    if id is not None:
        params['id'] = id
    if peer_id is not None:
        params['peer_id'] = peer_id
    if username is not None:
        params['username'] = username
    if url is not None:
        params['url'] = url
    
    resp = requests.put(f"{BASE_URL}/telegram/peers/unblock", params=params, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def telegram_peer_drop_all(subscriber: int) -> List[Dict]:
    resp = requests.put(f"{BASE_URL}/telegram/peers/drop_channels", params={'subscriber': subscriber}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def create_telegram_peer(peers: Dict[str, Any]) -> List[Dict]:
    resp = requests.post(f"{BASE_URL}/telegram/peers", json=peers, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def subscribe_telegram_peer(subscriber_number: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/peers/subscribe/{subscriber_number}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def unsubscribe_telegram_peer(
    id: Optional[int] = None,
    peer_id: Optional[int] = None,
    username: Optional[str] = None,
    url: Optional[str] = None
) -> Dict:
    params = {}
    if id is not None:
        params['id'] = id
    if peer_id is not None:
        params['peer_id'] = peer_id
    if username is not None:
        params['username'] = username
    if url is not None:
        params['url'] = url
    
    resp = requests.put(f"{BASE_URL}/telegram/peers/unsubscribe", params=params, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- Telegram channels Under Follow  -------------------------- #
def get_channels_underfollow_all() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/telegram/channels/underfollow/all", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_channel_underfollow(channel_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/channels/underfollow/channel/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_channels_underfollow_details() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/telegram/channels/underfollow/details/all", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_channel_underfollow(channel_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/telegram/channels/underfollow/channel/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def create_channel_underfollow(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/channels/underfollow", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_channel_underfollow(channel_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/channels/underfollow/{channel_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

# -------------------------- Telegram Users Under Follow  -------------------------- #

def get_users_underfollow_all() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/telegram/users/underfollow/all", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_underfollow(user_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/users/underfollow/user/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_user_underfollow(user_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/telegram/users/underfollow/user/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def create_user_underfollow(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/users/underfollow", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_user_underfollow(user_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/users/underfollow/{user_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- Users query Ids  -------------------------- #

def get_user_query_id_all() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/user/queries", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_query_id(query_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/user/queries/{query_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_user_query_id(query_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/user/queries/{query_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_user_query_id(query_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/user/queries/{query_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def create_user_query_id(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/user/queries", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

# -------------------------- User queries APIs  -------------------------- #

def create_user_query(data: List[Dict[str, Any]]) -> Dict:
    resp = requests.post(f"{BASE_URL}/user_query", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_query_all() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/user_query/all", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_query_by_id(id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/user_query/id/{id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_queries_by_user(user_id: str) -> Dict:
    resp = requests.get(f"{BASE_URL}/user_query/user/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_user_query(id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/user_query/id/{id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_user_query(id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/user_query/id/{id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- User channels APIs  -------------------------- #

def create_user_channel(data: List[Dict[str, Any]]) -> Dict:
    resp = requests.post(f"{BASE_URL}/user", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def toggle_channel_status(user_id) -> Dict:
    resp = requests.get(f"{BASE_URL}/user/status/toggle/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_channels() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/user_channel/all", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_channel_by_id(id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/user_channel/id/{id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_channel_by_user(user_id: str) -> Dict:
    resp = requests.get(f"{BASE_URL}/user_channel/user/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_channel_by_chat(chat_id: str) -> Dict:
    resp = requests.get(f"{BASE_URL}/user_channel/chat/{chat_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_user_channel(id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/user_channel/id/{id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_user_channel(id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/user_channel/id/{id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- User APIs  -------------------------- #

def create_user(data: List[Dict[str, Any]]) -> Dict:
    resp = requests.post(f"{BASE_URL}/users", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def toggle_user_status(user_id) -> Dict:
    resp = requests.put(f"{BASE_URL}/users/status/toggle/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_users() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/users", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_by_id(user_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/users/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_user_by_username(username: str) -> Dict:
    resp = requests.get(f"{BASE_URL}/users", params={'username': username}, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_user(user_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/users/{user_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_user(user_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/users/{user_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- Telegram channel APIs  -------------------------- #

def create_telegram_channel(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/channels", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_telegram_channel(channel_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/channels/{channel_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_telegram_channel(channel_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/telegram/channels/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_telegram_channels() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/telegram/channels", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_telegram_channel(channel_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/channels/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_telegram_channel_by_subscriber(phone) -> List:
    resp = requests.get(f"{BASE_URL}/telegram/channels_by_subscriber/{phone}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def  get_telegram_channel_by_id(chat_id) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/channels_by_id/{chat_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_telegram_channel_by_key(key) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/channels_by_key/{key}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def pick_telegram_channel() -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/channels/collect/up", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def drop_telegram_channel(channel_id: int) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/channels/collect/down/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def subscribe_telegram_channel(subscriber_number: int) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/channel/subscribe/{subscriber_number}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def unsubscribe_telegram_channel(channel_id: int) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/channel/unsubscribe/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- Telegram account APIs  -------------------------- #

def create_telegram_account(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/accounts", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_telegram_account(account_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/accounts/{account_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_telegram_account(account_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/telegram/accounts/{account_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_telegram_accounts() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/telegram/accounts", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_telegram_account(account_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/accounts/{account_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def pick_telegram_account() -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/accounts/process/up", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def drop_telegram_account(account_id: int) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/accounts/process/down/{account_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- Twitter channel APIs  -------------------------- #

def create_twitter_channel(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/twitter/channels", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_twitter_channel(channel_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/twitter/channels/{channel_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_twitter_channel(channel_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/twitter/channels/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_twitter_channels() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/twitter/channels", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_twitter_channel(channel_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/twitter/channels/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# -------------------------- Rss channel APIs  -------------------------- #

def create_rss_channel(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/rss/channels", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def update_rss_channel(channel_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/rss/channels/{channel_id}", json=data, timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def delete_rss_channel(channel_id: int) -> Dict:
    resp = requests.delete(f"{BASE_URL}/rss/channels/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_rss_channels() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/rss/channels", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_rss_channel(channel_id: int) -> Dict:
    resp = requests.get(f"{BASE_URL}/rss/channels/{channel_id}", timeout=30.0)
    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
