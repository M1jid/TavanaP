import socks
import json
from time import sleep

from utils.kafka_router import KafkaRouter
from utils.redis_wrapper import RedisWrapper

from utils.ksqldb_handler import KsqlDBHandler
from utils.ksqldb_config import get_ksqldb_config

ksql_config = get_ksqldb_config()
ksql_handler = KsqlDBHandler(**ksql_config)

from utils.elastic_handler import ElasticHandler
from utils.elastic_config import get_elastic_config

elastic_config = get_elastic_config()
elastic_handler = ElasticHandler(**elastic_config)

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(handler)


from app.config import (
    CONNECTOR_PATH,
    STREAMS_PATH,
    ELASTIC_INDEX_MAPPING_PATH,
    REDIS_HOST,
    REDIS_PORT,
    PROXY_PROTOCOL,
    PROXY_HOST,
    PROXY_PORT,
    KAFKA_BOOTSTRAP_SERVERS,
)


# ----- CREATE ELASTICSEARCH INDEXES -----
try:
    with open('app/conf/elastic_search_mapping.json', "r", encoding="utf-8") as file:
        configs = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise RuntimeError(f"Failed to load {ELASTIC_INDEX_MAPPING_PATH}: {e}")

index_names = [next(iter(config.values())).keys() for config in configs]
index_configs = [next(iter(config.values())).values() for config in configs]
index_names = [list(names)[0] for names in index_names]
index_configs = [list(values)[0] for values in index_configs]

# for index, index_config in zip(index_names, index_configs):
#     elastic_handler.create_index(index_name=index, body=index_config, check_exists=True)

async def init_elastic_indexes():
    logger.info("Initializing Elasticsearch indexes...")

    for index, index_config in zip(index_names, index_configs):
        logger.info(f"Creating index: {index}")
        success = await elastic_handler.create_index(
            index_name=index, body=index_config, check_exists=True
        )
        if success:
            logger.info(f"✅ Index '{index}' initialized successfully")
        else:
            logger.error(f"❌ Failed to initialize index '{index}'")

    logger.info("All Elasticsearch index initializations completed.")


# ----- CREATE KSQLDB CONNECTORS -----
try:
    with open('app/conf/connector.json', "r", encoding="utf-8") as file:
        configs = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise RuntimeError(f"Failed to load {CONNECTOR_PATH}: {e}")

connector_names = [list(config.keys())[0] for config in configs]
connector_configs = [list(config.values())[0] for config in configs]

for connector_name, connector_config in zip(connector_names, connector_configs):
    response =ksql_handler.create_sink_connector(
        connector_name=connector_name,
        connector_config=connector_config,
        check_exists=True,
    )
    if not response:
        logger.error(f"Failed to create connector '{connector_name}'")
        exit(1)
    else:
        logger.info(f"Connector '{connector_name}' created successfully")


# ----- CREATE KSQLDB TOPICS -----
response = ksql_handler.list_topics()
for topic in index_names:
    while topic not in response:
        sleep(1)
        logger.info(response)
        response = ksql_handler.list_topics()


# ----- CREATE KSQLDB STREAMS -----
try:
    with open('app/conf/stream.json', "r", encoding="utf-8") as file:
        configs = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise RuntimeError(f"Failed to load {CONNECTOR_PATH}: {e}")

stream_names = [list(config.keys())[0] for config in configs]
stream_configs = [list(config.values())[0] for config in configs]

for stream_name, stream_config in zip(stream_names, stream_configs):
    response = ksql_handler.create_stream(
        stream_name=stream_name,
        stream_config=stream_config,
        check_exists=True,
    )
    if not response:
        logger.error(f"Failed to create stream '{stream_name}'")
        exit(1)


# ----- Proxy -----
proxy_server = (
    socks.SOCKS5 if PROXY_PROTOCOL == "socks5h" else socks.HTTP,
    PROXY_HOST,
    PROXY_PORT,
    True
)


# ----- CREATE KAFKA ROUTER -----
kafka_router = KafkaRouter(kafka_host=KAFKA_BOOTSTRAP_SERVERS)

redis_db = RedisWrapper(REDIS_HOST, REDIS_PORT)


# ----- Exported symbols -----
__all__ = [
    "proxy_server",
    "ksql_handler",
    "elastic_handler",
    "redis_db",
    "kafka_router",
]