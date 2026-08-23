import socks
import json

from utils.redis_wrapper import RedisWrapper

from app.config import (
    REDIS_HOST,
    REDIS_PORT,
    PROXY_PROTOCOL,
    PROXY_HOST,
    PROXY_PORT,
)


# ----- Proxy -----
proxy_server = (
    socks.SOCKS5 if PROXY_PROTOCOL == "socks5h" else socks.HTTP,
    PROXY_HOST,
    PROXY_PORT,
    True,
)

redis_db = RedisWrapper(REDIS_HOST, REDIS_PORT)

# ----- Exported symbols -----
__all__ = [
    "redis_db",
    "proxy_server",
]
