from dotenv import load_dotenv
import os


load_dotenv()


# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", None)

# KSQL Configuration
KSQL_HOST = os.getenv("KSQL_HOST", None)
STREAMS_PATH = os.getenv("RSS_STREAMS_PATH", None)
CONNECTOR_PATH = os.getenv("RSS_CONNECTOR_PATH", None)

# Elasticsearch Configuration
ELASTIC_URL = os.getenv("ELASTIC_URL", None)
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", None)
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME", None)
ELASTIC_INDEX_MAPPING_PATH = os.getenv("RSS_ELASTIC_INDEX_MAPPING_PATH", None)

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", None)
REDIS_PORT = os.getenv("REDIS_PORT", None)

# Proxy Configuration
PROXY_HOST = os.getenv("PROXY_HOST", None)
PROXY_PORT = os.getenv("PROXY_PORT", None)
PROXY_PROTOCOL = os.getenv("PROXY_PROTOCOL", None)

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", None)
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", None)
OLLAMA_SENTIMENT_MODEL = os.getenv("OLLAMA_SENTIMENT_MODEL", None)

# Telegram Configuration
TELEGRAM_TOPIC = os.getenv("RSS_MESSAGE_TO_TELEGRAM_TOPIC", None)

# Authentication Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
