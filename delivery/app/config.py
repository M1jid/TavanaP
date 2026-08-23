from dotenv import load_dotenv
import os


load_dotenv()


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", None)
KAFKA_TOPIC = os.getenv("TELEGRAM_MESSAGE_TO_TELEGRAM_TOPIC", None)

ETA_KAFKA_GROUP_ID = os.getenv("ETA_KAFKA_GROUP_ID", None)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", None)
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", None)
OLLAMA_SENTIMENT_MODEL = os.getenv("OLLAMA_SENTIMENT_MODEL", None)

REDIS_HOST = os.getenv("REDIS_HOST", None)
REDIS_PORT = os.getenv("REDIS_PORT", None)

PROXY_HOST = os.getenv("PROXY_HOST", None)
PROXY_PORT = int(os.getenv("PROXY_PORT", None))
PROXY_PROTOCOL = os.getenv("PROXY_PROTOCOL", None)
