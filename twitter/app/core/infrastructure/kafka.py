"""
Kafka infrastructure management for the Telegram application.

This module handles Kafka setup, stream creation, and connector management.
"""

import logging
from time import sleep
from typing import List, Dict, Any

from utils.ksqldb_handler import KsqlDBHandler
from utils.ksqldb_config import get_ksqldb_config
from app.core.config import settings
from app.core.config.kafka_configs import KAFKA_STREAM_DEFINITIONS, KAFKA_CONNECTOR_DEFINITIONS

logger = logging.getLogger(__name__)


class KafkaInfrastructure:
    """Manages Kafka infrastructure setup and teardown."""
    
    def __init__(self):
        self.ksql_config = get_ksqldb_config()
        self.ksql_handler = KsqlDBHandler(**self.ksql_config)
    
    async def setup_streams(self) -> bool:
        """Create Kafka streams from configuration."""
        logger.info("Setting up Kafka streams...")
        
        for stream in KAFKA_STREAM_DEFINITIONS:
            response = self.ksql_handler.create_stream(
                stream_name=stream['name'],
                stream_config=stream['config'],
                check_exists=True,
            )
            if not response:
                logger.error(f"Failed to create stream '{stream['name']}'")
                return False
        
        logger.info("Kafka streams setup completed successfully")
        return True
    
    async def setup_connectors(self) -> bool:
        """Create Kafka connectors from configuration."""
        logger.info("Setting up Kafka connectors...")
        
        for connector in KAFKA_CONNECTOR_DEFINITIONS:
            response = self.ksql_handler.create_sink_connector(
                connector_name=connector['name'],
                connector_config=connector['config'],
                check_exists=True,
            )
            if not response:
                logger.error(f"Failed to create connector '{connector['name']}'")
                return False
        
        logger.info("Kafka connectors setup completed successfully")
        return True
    
    async def wait_for_topics(self) -> bool:
        """Wait for all required topics to be available."""
        logger.info("Waiting for Kafka topics to be available...")
        
        for topic in settings.ALL_TELEGRAM_TOPIC_NAME:
            while topic not in self.ksql_handler.list_topics():
                logger.info(f"Topic '{topic}' not found in ksqlDB")
                sleep(1)
        
        logger.info("All Kafka topics are available")
        return True
    
    async def create_middle_connectors(self, connectors: List[str]) -> bool:
        """Create middle connectors for Kafka."""
        logger.info("Creating middle connectors for Kafka...")

        for connector in connectors:
            self.ksql_handler.create_sink_connector(
                connector_name=f"{connector}_middle_connector",
                connector_config = f"""
                        CREATE SOURCE CONNECTOR {connector}_middle_connector WITH (
                        'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
                        'connection.url'= '{settings.ELASTICSEARCH_HOSTS}',
                        'connection.username'= '{settings.ELASTICSEARCH_USERNAME}', 'connection.password' = '{settings.ELASTICSEARCH_PASSWORD}',
                        'connection.ssl.enabled'= 'true', 'connection.ssl.truststore.location'= '/certs/kafka.truststore.jks',
                        'connection.ssl.truststore.password'= 'change-me',
                        'connection.ssl.truststore.type'= 'JKS',
                        'key.ignore'= 'false',
                        'type.name'= '_doc',
                        'topics'= '{connector}_middle_topic',
                        'transforms.setTimestampType.type'= 'org.apache.kafka.connect.transforms.TimestampConverter$Value',
                        'transforms.setTimestampType.field'= 'date',
                        'transforms.setTimestampType.target.type'= 'Timestamp',
                        'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
                        'value.converter.schemas.enable'= 'false',
                        'schema.ignore'= 'true',
                        'tasks.max'= '1',
                        'ksql.insert.into.values.enabled'= 'true',
                        'transforms' = 'RenameIndex',
                        'transforms.RenameIndex.type' = 'org.apache.kafka.connect.transforms.RegexRouter',
                        'transforms.RenameIndex.regex' = '{connector}_middle_topic',
                        'transforms.RenameIndex.replacement' = '{settings.TELEGRAM_MESSAGES_TOPIC_NAME}'
                    );
                """,
                check_exists=True,
            )

        logger.info("Middle connectors created successfully")
        return True

    async def wait_for_middle_topics(self, topics: List[str]) -> bool:
        """Wait for all middle topics to be available."""
        logger.info("Waiting for Kafka middle topics to be available...")
        
        for topic in topics:
            while f'{topic}_middle_topic' not in self.ksql_handler.list_topics():
                logger.info(f"Topic '{topic}_middle_topic' not found in ksqlDB")
                sleep(1)
        
        logger.info("All Kafka middle topics are available")
        return True

    async def create_middle_streams(self, streams: List[str]) -> bool:
        """Create middle streams for Kafka."""
        logger.info("Creating middle streams for Kafka...")
        stream_config = f"""
                CREATE STREAM {f'{stream}_middle_stream'} (
                ID STRING KEY,
                PRIVATE_URL STRING,
                PUBLIC_URL STRING,
                PEER_ID BIGINT,
                PEER_TYPE STRING,
                MESSAGE_ID BIGINT,
                TYPE STRING,
                FETCH_TIME BIGINT,
                DATE STRING ,
                REPLY_PEER_ID BIGINT,
                REPLY_LINK STRING,
                REPLY_PEER_TYPE STRING,
                FWD_PEER_ID BIGINT,
                FWD_LINK STRING,
                FWD_PEER_TYPE STRING,
                AUTHOR_ID BIGINT,
                AUTHOR_TYPE STRING,
                SENTIMENT STRING,
                SENSE STRING,
                TAGS ARRAY<VARCHAR>,
                VIEWS_COUNT BIGINT,
                FORWARDS_COUNT BIGINT,
                REACTIONS_COUNT BIGINT,
                REPLIES_COUNT BIGINT,
                CLEANED_MESSAGE STRING,
                REACTIONS ARRAY<STRUCT<EMOJI STRING, COUNT BIGINT>>,
                MESSAGE STRING,
                MEDIA ARRAY<VARCHAR> ,
                LINKS ARRAY<VARCHAR>,
                MENTIONS ARRAY<VARCHAR>,
                HASHTAGS ARRAY<VARCHAR>,
                BOLDED_PARTS ARRAY<VARCHAR>,
                STRIKETHROUGHT_PARTS ARRAY<VARCHAR>,
                MONOSPACE_PARTS ARRAY<VARCHAR>,
                SPOILER_PARTS ARRAY<VARCHAR>,
                BLOCKQUOTE_PARTS ARRAY<VARCHAR>,
                STRIKETHROUGHED_PARTS ARRAY<VARCHAR>, CODES ARRAY<VARCHAR>
            )
            WITH (
                KAFKA_TOPIC= '{f'{stream}_middle_topic'}', VALUE_FORMAT= 'JSON'
            );
        """
        for stream in streams:
            self.ksql_handler.create_stream(stream_name=f'{stream}_middle_stream', stream_config=stream_config, check_exists=True)
        
        logger.info("All Kafka middle streams are available")
        return True

    async def setup(self) -> bool:
        """Complete Kafka infrastructure setup."""
        try:
            # Setup connectors
            if not await self.setup_connectors():
                return False
            
            # Wait for topics first
            if not await self.wait_for_topics():
                return False
            
            # Setup streams
            if not await self.setup_streams():
                return False
            
            logger.info("Kafka infrastructure setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Kafka infrastructure: {e}")
            return False
    
    def get_handler(self) -> KsqlDBHandler:
        """Get the KsqlDB handler instance."""
        return self.ksql_handler
