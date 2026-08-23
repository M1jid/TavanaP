"""
Kafka configuration definitions for the Telegram application.

This module contains:
- Kafka stream definitions
- Kafka connector definitions
"""

from app.core.config import settings

# Kafka Stream Definitions
KAFKA_STREAM_DEFINITIONS = [
    {
        "name": f"{settings.STREAM_TELEGRAM_MESSAGES}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_MESSAGES} (
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
                KAFKA_TOPIC= '{settings.TELEGRAM_MESSAGES_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
    {
        "name": f"{settings.STREAM_TELEGRAM_CHANNELS}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_CHANNELS} (
                ID STRING KEY,
                FETCH_TIME BIGINT,
                TYPE STRING,
                PEER_ID BIGINT,
                USERNAME STRING,
                TITLE STRING,
                DESCRIPTION STRING,
                URL STRING,
                FOLLOWERS ARRAY<STRUCT<FOLLOWERS BIGINT,
                FETCH_TIME STRING>>,
                TAG ARRAY<VARCHAR>,
                LINKED_GROUP_TITLE STRING,
                LINKED_GROUP_USERNAME STRING,
                LINKED_GROUP_ID BIGINT,
                AVAILABLE_REACTIONS ARRAY<VARCHAR>,
                CAN_VIEW_PARTICIPANTS BOOLEAN
            )
            WITH (
                KAFKA_TOPIC= '{settings.TELEGRAM_CHANNELS_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
    {
        "name": f"{settings.STREAM_TELEGRAM_GROUPS}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_GROUPS} (
                ID STRING KEY,
                PEER_ID BIGINT,
                FETCH_TIME BIGINT,
                USERNAME STRING,
                URL STRING,
                TITLE STRING,
                DESCRIPTION STRING,
                AVAILABLE_REACTIONS ARRAY<VARCHAR>,
                FOLLOWERS ARRAY<STRUCT<FOLLOWERS BIGINT,
                TAG ARRAY<VARCHAR>,
                CAN_VIEW_PARTICIPANTS BOOLEAN
                LINKED_CHANNEL_ID BIGINT,
                LINKED_CHANNEL_TITLE STRING,
                LINKED_CHANNEL_USERNAME STRING,
            )
            WITH (
                KAFKA_TOPIC= '{settings.TELEGRAM_GROUPS_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
    {
        "name": f"{settings.STREAM_TELEGRAM_USERS}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_USERS} (
                ID STRING KEY,
                USER_ID BIGINT,
                FETCH_TIME BIGINT,
                USERNAME STRING,
                PHONE STRING,
                FIRST_NAME STRING,
                LAST_NAME STRING,
                BIO STRING,
                PRIVATE_FORWARD_NAME STRING,
                BIRTHDAY STRING,
                PERSONAL_CHANNEL_ID BIGINT,
                PERSONAL_CHANNEL_TITLE STRING
            )
            WITH (
                KAFKA_TOPIC= '{settings.TELEGRAM_USERS_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
    {
        "name": f"{settings.STREAM_TELEGRAM_BOTS}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_BOTS} (
                ID STRING KEY,
                FETCH_TIME BIGINT,
                USERNAME STRING,
                PHONE STRING,
                FIRST_NAME STRING,
                LAST_NAME STRING,
                BIO STRING,
                PRIVATE_FORWARD_NAME STRING,
                BIRTHDAY STRING,
                PERSONAL_CHANNEL_ID BIGINT,
                PERSONAL_CHANNEL_TITLE STRING,
                URL STRING,
            ) 
            WITH (
                KAFKA_TOPIC= '{settings.TELEGRAM_BOTS_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
    {
        "name": f"{settings.STREAM_TELEGRAM_CHATS}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_CHATS} (
                ID STRING KEY, 
                MEDIA STRING, 
                GROUPED_ID STRING, 
                OUT BOOLEAN, 
                ADMIN_PEER_ID BIGINT, 
                FETCH_TIME BIGINT, 
                DATE STRING, 
                EDIT_DATE STRING, 
                TYPE STRING, 
                AUTHOR_ID BIGINT, 
                AUTHOR_TYPE STRING, 
                PEER_ID BIGINT, 
                PEER_TYPE STRING, 
                URL STRING, 
                MESSAGE_ID BIGINT, 
                MESSAGE STRING, 
                REPLY_PEER_TYPE STRING, 
                REPLY_PEER_ID BIGINT, 
                REPLY_LINK STRING, 
                FWD_PEER_TYPE STRING, 
                FWD_PEER_ID BIGINT, 
                TEXT_REACTIONS ARRAY<STRING>, 
                TAGS ARRAY<VARCHAR>, 
                SENTIMENT STRING, 
                SENSE STRING, 
                CLEANED_MESSAGE STRING, 
                LINKS ARRAY<VARCHAR>, 
                MENTIONS ARRAY<VARCHAR>, 
                HASHTAGS ARRAY<VARCHAR>, 
                BOLDED_PARTS ARRAY<VARCHAR>, 
                STRIKETHROUGHT_PARTS ARRAY<VARCHAR>, 
                MONOSPACE_PARTS ARRAY<VARCHAR>, 
                SPOILER_PARTS ARRAY<VARCHAR>, 
                BLOCKQUOTE_PARTS ARRAY<VARCHAR>, 
                STRIKETHROUGHED_PARTS ARRAY<VARCHAR>, 
                CODES ARRAY<VARCHAR>
            )
            WITH (
                KAFKA_TOPIC= '{settings.TELEGRAM_CHATS_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
    {
        "name": f"{settings.STREAM_TELEGRAM_TEST}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_TEST} (
                ID STRING KEY
                MESSAGE STRING,
            )
            WITH (
                KAFKA_TOPIC= '{settings.TELEGRAM_TEST_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
    {
        "name": f"{settings.STREAM_TELEGRAM_TEST2}",
        "config": f"""
            CREATE STREAM {settings.STREAM_TELEGRAM_TEST2} (
                ID STRING KEY
                MESSAGE STRING,
            )
            WITH (
                KAFKA_TOPIC= '{settings.TELEGRAM_TEST2_TOPIC_NAME}', VALUE_FORMAT= 'JSON'
            );
        """
    },
]

# Kafka Connector Definitions
KAFKA_CONNECTOR_DEFINITIONS = [
    {
        "name": f"{settings.SINK_ELASTIC_TELEGRAM_MESSAGE_CONNECTOR}",
        "config": f"""
            CREATE SOURCE CONNECTOR {settings.SINK_ELASTIC_TELEGRAM_MESSAGE_CONNECTOR} WITH (
                'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
                'connection.url'= '{settings.ELASTICSEARCH_HOSTS}',
                'connection.username'= '{settings.ELASTICSEARCH_USERNAME}', 'connection.password' = '{settings.ELASTICSEARCH_PASSWORD}',
                'connection.ssl.enabled'= 'true', 'connection.ssl.truststore.location'= '/certs/kafka.truststore.jks',
                'connection.ssl.truststore.password'= 'change-me',
                'connection.ssl.truststore.type'= 'JKS',
                'key.ignore'= 'false',
                'type.name'= '_doc',
                'topics'= '{settings.TELEGRAM_MESSAGES_TOPIC_NAME}',
                'transforms.setTimestampType.type'= 'org.apache.kafka.connect.transforms.TimestampConverter$Value',
                'transforms.setTimestampType.field'= 'date',
                'transforms.setTimestampType.target.type'= 'Timestamp',
                'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
                'value.converter.schemas.enable'= 'false',
                'schema.ignore'= 'true',
                'tasks.max'= '1',
                'ksql.insert.into.values.enabled'= 'true'
            );
        """
    },
    {
        "name": f"{settings.SINK_ELASTIC_TELEGRAM_PEER_CONNECTOR}",
        "config": f"""
            CREATE SOURCE CONNECTOR {settings.SINK_ELASTIC_TELEGRAM_PEER_CONNECTOR} WITH (
                'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
                'connection.url'= '{settings.ELASTICSEARCH_HOSTS}',
                'connection.username'= '{settings.ELASTICSEARCH_USERNAME}', 'connection.password' = '{settings.ELASTICSEARCH_PASSWORD}',
                'connection.ssl.enabled'= 'true', 'connection.ssl.truststore.location'= '/certs/kafka.truststore.jks',
                'connection.ssl.truststore.password'= 'change-me',
                'connection.ssl.truststore.type'= 'JKS',
                'key.ignore'= 'false',
                'type.name'= '_doc',
                'topics'= '{settings.TELEGRAM_CHANNELS_TOPIC_NAME},{settings.TELEGRAM_GROUPS_TOPIC_NAME},{settings.TELEGRAM_USERS_TOPIC_NAME},{settings.TELEGRAM_BOTS_TOPIC_NAME}',
                'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
                'value.converter.schemas.enable'= 'false',
                'schema.ignore'= 'true',
                'tasks.max'= '1',
                'ksql.insert.into.values.enabled'= 'true'
            );
        """
    },
    {
        "name": f"{settings.SINK_ELASTIC_TELEGRAM_TEST_CONNECTOR}",
        "config": f"""
            CREATE SOURCE CONNECTOR {settings.SINK_ELASTIC_TELEGRAM_TEST_CONNECTOR} WITH (
                'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
                'connection.url'= '{settings.ELASTICSEARCH_HOSTS}',
                'connection.username'= '{settings.ELASTICSEARCH_USERNAME}', 'connection.password' = '{settings.ELASTICSEARCH_PASSWORD}',
                'connection.ssl.enabled'= 'true', 'connection.ssl.truststore.location'= '/certs/kafka.truststore.jks',
                'connection.ssl.truststore.password'= 'change-me',
                'connection.ssl.truststore.type'= 'JKS',
                'key.ignore'= 'false',
                'type.name'= '_doc',
                'topics'= '{settings.TELEGRAM_TEST_TOPIC_NAME}',
                'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
                'value.converter.schemas.enable'= 'false',
                'schema.ignore'= 'true',
                'tasks.max'= '1',
                'ksql.insert.into.values.enabled'= 'true'
            );
        """
    },
    {
        "name": f"{settings.SINK_ELASTIC_TELEGRAM_TEST2_CONNECTOR}",
        "config": f"""
            CREATE SOURCE CONNECTOR {settings.SINK_ELASTIC_TELEGRAM_TEST2_CONNECTOR} WITH (
                'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
                'connection.url'= '{settings.ELASTICSEARCH_HOSTS}',
                'connection.username'= '{settings.ELASTICSEARCH_USERNAME}', 'connection.password' = '{settings.ELASTICSEARCH_PASSWORD}',
                'connection.ssl.enabled'= 'true', 'connection.ssl.truststore.location'= '/certs/kafka.truststore.jks',
                'connection.ssl.truststore.password'= 'change-me',
                'connection.ssl.truststore.type'= 'JKS',
                'key.ignore'= 'false',
                'type.name'= '_doc',
                'topics'= '{settings.TELEGRAM_TEST2_TOPIC_NAME}',
                'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
                'value.converter.schemas.enable'= 'false',
                'schema.ignore'= 'true',
                'tasks.max'= '1',
                'ksql.insert.into.values.enabled'= 'true',
                'transforms' = 'RenameIndex',
                'transforms.RenameIndex.type' = 'org.apache.kafka.connect.transforms.RegexRouter',
                'transforms.RenameIndex.regex' = '{settings.TELEGRAM_TEST2_TOPIC_NAME}',
                'transforms.RenameIndex.replacement' = '{settings.TELEGRAM_TEST_TOPIC_NAME}'
            );
        """
    },
]

__all__ = ["KAFKA_STREAM_DEFINITIONS", "KAFKA_CONNECTOR_DEFINITIONS"]
