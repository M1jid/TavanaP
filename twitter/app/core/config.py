from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import logging

# --- Logging setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(handler)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

if not ENV_PATH.exists():
    logger.warning(f".env file not found at {ENV_PATH}")
    exit(1)

load_dotenv(ENV_PATH)


class Settings(BaseSettings):

    # KSQLDB STREAMS
    STREAM_TELEGRAM_MESSAGES: str
    STREAM_TELEGRAM_CHANNELS: str
    STREAM_TELEGRAM_GROUPS: str
    STREAM_TELEGRAM_USERS: str
    STREAM_TELEGRAM_BOTS: str
    STREAM_TELEGRAM_CHATS: str
    STREAM_TELEGRAM_MESSAGES: str
    STREAM_TELEGRAM_TEST: str
    STREAM_TELEGRAM_TEST2: str

    # KSQLDB CONNECTORS
    SINK_ELASTIC_TELEGRAM_MESSAGE_CONNECTOR: str
    SINK_ELASTIC_TELEGRAM_PEER_CONNECTOR: str
    SINK_ELASTIC_TELEGRAM_TEST_CONNECTOR: str
    SINK_ELASTIC_TELEGRAM_TEST2_CONNECTOR: str

    # KAFKA TOPICS
    TELEGRAM_MESSAGES_TOPIC_NAME: str
    TELEGRAM_CHATS_TOPIC_NAME: str
    TELEGRAM_CHANNELS_TOPIC_NAME: str
    TELEGRAM_GROUPS_TOPIC_NAME: str
    TELEGRAM_USERS_TOPIC_NAME: str
    TELEGRAM_BOTS_TOPIC_NAME: str
    TELEGRAM_TEST_TOPIC_NAME: str
    TELEGRAM_TEST2_TOPIC_NAME: str

    @property
    def ALL_TELEGRAM_TOPIC_NAME(self) -> list[str]:
        return [
            self.TELEGRAM_MESSAGES_TOPIC_NAME,
            self.TELEGRAM_CHATS_TOPIC_NAME,
            self.TELEGRAM_CHANNELS_TOPIC_NAME,
            self.TELEGRAM_GROUPS_TOPIC_NAME,
            self.TELEGRAM_USERS_TOPIC_NAME,
            self.TELEGRAM_BOTS_TOPIC_NAME,
            self.TELEGRAM_TEST_TOPIC_NAME,
            self.TELEGRAM_TEST2_TOPIC_NAME
        ]

    KAFKA_BOOTSTRAP_SERVERS: str
    TELEGRAM_CHATS_MESSAGE_SEND_TOPIC: str
    TELEGRAM_UPDATE_MESSAGE: str
    TELEGRAM_UPDATE_ACK_TOPIC: str

    TELEGRAM_CONNECTOR_PATH: str
    TELEGRAM_STREAMS_PATH: str

    TELEGRAM_ELASTIC_INDEX_MAPPING_PATH: str
    KSQL_HOST: str

    OLLAMA_HOST: str
    OLLAMA_API_KEY: str
    OLLAMA_SENTIMENT_MODEL: str

    REDIS_HOST: str
    REDIS_PORT: int
    PROXY_HOST: str
    PROXY_PORT: int
    PROXY_PROTOCOL: str
    TELEGRAM_SESSION_PATH: str

    MINIO_TELEGRAM_MEDIA_CHATS_BUCKET_NAME: str
    MINIO_TELEGRAM_CHANNEL_BUCKET_NAME: str
    MINIO_TELEGRAM_GROUP_BUCKET_NAME: str
    MINIO_TELEGRAM_USER_BUCKET_NAME: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str  
    POSTGRES_PORT: int
    POSTGRES_DB: str

    ELASTICSEARCH_HOSTS: str
    ELASTICSEARCH_USERNAME: str
    ELASTICSEARCH_PASSWORD: str

settings = Settings()
