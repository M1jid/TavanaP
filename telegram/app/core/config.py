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
    STREAM_TWITTER_MESSAGES: str
    STREAM_TWITTER_PAGES: str

    # KSQLDB CONNECTORS
    SINK_ELASTIC_TWITTER_MESSAGE_CONNECTOR: str
    SINK_ELASTIC_TWITTER_PAGE_CONNECTOR: str

    # KAFKA TOPICS
    TWITTER_MESSAGES_TOPIC_NAME: str
    TWITTER_PAGES_TOPIC_NAME: str

    @property
    def ALL_TWITTER_TOPIC_NAME(self) -> list[str]:
        return [
            self.TWITTER_MESSAGES_TOPIC_NAME,
            self.TWITTER_PAGES_TOPIC_NAME,
        ]

    KAFKA_BOOTSTRAP_SERVERS: str

    KSQL_HOST: str

    OLLAMA_HOST: str
    OLLAMA_API_KEY: str
    OLLAMA_SENTIMENT_MODEL: str

    REDIS_HOST: str
    REDIS_PORT: int
    PROXY_HOST: str
    PROXY_PORT: int
    PROXY_PROTOCOL: str

    MINIO_TWITTER_MEDIA_BUCKET_NAME: str
    MINIO_TWITTER_PAGES_BUCKET_NAME: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str  
    POSTGRES_PORT: int
    POSTGRES_DB: str

    ELASTICSEARCH_HOSTS: str
    ELASTICSEARCH_USERNAME: str
    ELASTICSEARCH_PASSWORD: str

settings = Settings()
