from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
import logging
import os
import signal


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {"Content-Type": "application/vnd.ksql.v1+json"}

# ksqlDB manager class
class KsqlDBManager:
    def __init__(self, ksqldb_url):
        self.ksqldb_url = ksqldb_url

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def execute_ksql_query(self, query):
        """Execute a ksqlDB query."""
        try:
            payload = {"ksql": query, "streamsProperties": {}}
            logger.info(payload)
            response = requests.post(self.ksqldb_url, headers=HEADERS, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error executing ksql query2: {e}")  # e is undefined here
        except requests.exceptions.RequestException as e:
            logger.error(f"Error executing ksql query: {e}")
            # raise  # let the retry mechanism take over

    def create_stream(self, stream_name, stream_config):
        """Create a stream in ksqlDB."""

        # Check if the stream already exists
        query = "SHOW STREAMS;"
        response = self.execute_ksql_query(query)

        existing_streams = [
            stream['name'] for stream in response[0]['streams']
        ]

        if stream_name in existing_streams:
            logger.info(f"Stream '{stream_name}' already exists. Skipping creation.")
            return

        # Creating an stream
        response = self.execute_ksql_query(stream_config)
        return response

    def create_sink_connector(self, connector_name, connector_config):
        """Create a sink connector in ksqlDB if it doesn't already exist."""
        # Query to check if the connector already exists
        query = f"SHOW CONNECTORS;"
        response = self.execute_ksql_query(query)

        # Check existing connectors in the response
        existing_connectors = [
            connector['name'] for connector in response[0]['connectors']
        ]

        if connector_name in existing_connectors:
            logger.info(f"Connector '{connector_name}' already exists. Skipping creation.")
            return

        # Create connector if not found
        response = self.execute_ksql_query(connector_config)
        return response

    def insert_data(self, stream_name, data):
        """Insert data into a ksqlDB stream."""
        values = ''
        for val in data.values():
            if isinstance(val, int):
                values += f', {str(val)}'
            if isinstance(val, str):
                values += f", '{val}'"
            if isinstance(val, dict):
                if len(list(val.keys())) == 0:
                    values += ", NULL"
                else:
                    values += ', MAP ('
                    metadata = ''
                    for key_dict, value_dict in val.items():
                        metadata += f",'{key_dict}':={str(value_dict)}"
                    metadata = metadata[1:]
                    values += f'{metadata})'
            if isinstance(val, list):
                if len(val) == 0:
                    values += ", NULL"
                else:
                    values += ', ARRAY['
                    metadata = ''
                    for item in val:
                        metadata += f", '{item}'"
                    metadata = metadata[1:]
                    values += f'{metadata}]'
            if val is None:
                values += ", NULL"
        values = values[1:]
        keys = ", ".join([f"{k}" if isinstance(k, str) else str(k) for k in data.keys()])
        query = f"INSERT INTO {stream_name} ({keys}) VALUES ({values});"
        logger.info(query)
        self.execute_ksql_query(query)


def ksql_manager_setup(
    connector_configs: str,
    connector_names: str,
    stream_configs: str,
    stream_names: list,
    topics: str,
    ksql_url: str,
):
    manager = KsqlDBManager(ksql_url)

    for connector_name, connector_config in zip(connector_names, connector_configs):
        logger.info('----------------------------')
        logger.info(connector_name)
        manager.create_sink_connector(
            connector_name=connector_name,
            connector_config=connector_config,
        )

    response = manager.execute_ksql_query('SHOW TOPICS;')
    for topic in topics:
        while topic not in [topic['name'] for topic in response[0]['topics']]:
            logger.info(topics)
            response = manager.execute_ksql_query('SHOW TOPICS;')
            logger.info([topic['name'] for topic in response[0]['topics']])

    for stream_name, stream_config in zip(stream_names, stream_configs):
        logger.info('----------------------------')
        logger.info(stream_name)
        manager.create_stream(
            stream_name=stream_name,
            stream_config=stream_config
        )

    return manager
