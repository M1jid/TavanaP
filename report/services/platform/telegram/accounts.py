import requests
import fastapi

from app.config import TELEGRAM_ACCOUNT_MANAGER_HOST

def send_code(phone: str):
    try:
        resp = requests.post(
            f"{TELEGRAM_ACCOUNT_MANAGER_HOST}/send_code",
            json={"phone": phone},
            timeout=30.0,
        )
    except requests.exceptions.ConnectionError:
        raise fastapi.HTTPException(
            status_code=503, detail="Telegram account manager service unavailable"
        )
    except requests.exceptions.Timeout:
        raise fastapi.HTTPException(
            status_code=504, detail="Telegram account manager service timed out"
        )

    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def verify_code(phone: str, code: str):
    try:
        resp = requests.post(
            f"{TELEGRAM_ACCOUNT_MANAGER_HOST}/verify_code",
            json={"phone": phone, "code": code},
            timeout=30.0,
        )
    except requests.exceptions.ConnectionError:
        raise fastapi.HTTPException(
            status_code=503, detail="Telegram account manager service unavailable"
        )
    except requests.exceptions.Timeout:
        raise fastapi.HTTPException(
            status_code=504, detail="Telegram account manager service timed out"
        )

    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def verify_password(phone: str, password: str):
    try:
        resp = requests.post(
            f"{TELEGRAM_ACCOUNT_MANAGER_HOST}/verify_password",
            json={"phone": phone, "password": password},
            timeout=30.0,
        )
    except requests.exceptions.ConnectionError:
        raise fastapi.HTTPException(
            status_code=503, detail="Telegram account manager service unavailable"
        )
    except requests.exceptions.Timeout:
        raise fastapi.HTTPException(
            status_code=504, detail="Telegram account manager service timed out"
        )

    if resp.status_code != 200:
        raise fastapi.HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
