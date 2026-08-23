from telethon import TelegramClient
from telethon.errors import PhoneCodeInvalidError, SessionPasswordNeededError, PasswordHashInvalidError, PhoneNumberInvalidError

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import socks

from config import PROXY_HOST, PROXY_PORT, PROXY_PROTOCOL, SESSION_PATH

app = FastAPI()

api_id = 2040
api_hash = "b18441a1ff607e10a989891a5462e627"
clients = {}

proxy = (socks.SOCKS5 if PROXY_PROTOCOL == "socks5" else socks.HTTP, PROXY_HOST, PROXY_PORT)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneRequest(BaseModel):
    phone: str

@app.post("/send_code")
async def send_code(request: PhoneRequest):
    logger.info(request.phone)
    phone = request.phone
    client = TelegramClient(f"{SESSION_PATH}/{phone}.session", api_id, api_hash, proxy=proxy)
    await client.connect()

    if await client.is_user_authorized():
        await client.disconnect()
        return {"detail": "Already logged in"}

    try:
        await client.send_code_request(phone)
    except PhoneNumberInvalidError:
        await client.disconnect()
        raise HTTPException(status_code=400, detail="Invalid phone number")

    clients[phone] = client
    return {"detail": "Code sent"}


class VerifyCodeRequest(BaseModel):
    phone: str
    code: str

@app.post("/verify_code")
async def verify_code(request: VerifyCodeRequest):
    phone = request.phone
    code = request.code
    client = clients.get(phone)
    if not client:
        raise HTTPException(400, "No session found for phone")
    try:
        await client.sign_in(phone, code)
        if await client.is_user_authorized():
            await client.disconnect()
        return {"detail": "Signed in successfully"}
    except PhoneCodeInvalidError:
        raise HTTPException(400, "Invalid verification code")
    except SessionPasswordNeededError:
        return {"detail": "Need password"}
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")

class VerifyPasswordRequest(BaseModel):
    phone: str
    password: str

@app.post("/verify_password")
async def verify_password(request: VerifyPasswordRequest):
    phone = request.phone
    password = request.password
    client = clients.get(phone)
    if not client:
        raise HTTPException(400, "No session found for phone")
    try:
        await client.sign_in(password=password)
        if await client.is_user_authorized():
            await client.disconnect()
        return {"detail": "Signed in successfully"}
    except PasswordHashInvalidError:
        raise HTTPException(400, "Invalid password")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")
