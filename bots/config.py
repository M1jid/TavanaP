import os
import socks
from routing_roles import config

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("TELEGRAM_ACCOUNT_MANAGER_HOST", "http://127.0.0.1:9000")

PROXY = {
    "https": os.getenv("TELEGRAM_BOT_PROXY", "http://127.0.0.1:10809")
}

# Comma-separated Telegram user IDs allowed to use the admin bot
USER_IDS = [
    int(x.strip())
    for x in os.getenv("TELEGRAM_BOT_ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]
