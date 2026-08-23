# ----- Elastic handler -----
from utils.elastic_handler import ElasticHandler
from utils.elastic_config import get_elastic_config

elastic_config = get_elastic_config()
elastic_handler = ElasticHandler(**elastic_config)

# ----- Kafka handler -----
from utils.kafka_handler import KafkaHandler
from utils.kafka_router import KafkaRouter
from app.config import KAFKA_BOOTSTRAP_SERVERS

kafka_router = KafkaRouter(kafka_host=KAFKA_BOOTSTRAP_SERVERS)
kafka_producer = KafkaHandler()

# ----- MinIO handler -----
from utils.minio_handler import MinIOHandler
from utils.minio_config import get_minio_config

minio_config = get_minio_config(type='channel')
minio_handler = MinIOHandler(**minio_config)

from utils.redis_handler import RedisHandler
from utils.redis_config import get_redis_config

redis_config = get_redis_config()
redis_handler = RedisHandler(**redis_config)

__all__ = [
    "elastic_handler",
    "kafka_router",
    "kafka_producer",
    "minio_handler",
    "redis_handler",
]
