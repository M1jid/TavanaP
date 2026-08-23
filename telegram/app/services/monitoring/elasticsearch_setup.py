"""
Setup Elasticsearch index template for Telegram monitoring
"""
import asyncio
from app.startup import elastic_handler

async def setup_telegram_monitoring_index():
    """Create index template for Telegram monitoring"""
    
    index_template = {
        "index_patterns": ["telegram-monitoring*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index": {
                    "refresh_interval": "5s"
                }
            },
            "mappings": {
                "properties": {
                    "timestamp": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "account_id": {
                        "type": "keyword"
                    },
                    "phone": {
                        "type": "keyword"
                    },
                    "operation": {
                        "type": "keyword"
                    },
                    "status": {
                        "type": "keyword"
                    },
                    "level": {
                        "type": "keyword"
                    },
                    "message": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "channel_id": {
                        "type": "keyword"
                    },
                    "channel_username": {
                        "type": "keyword"
                    },
                    "message_count": {
                        "type": "integer"
                    },
                    "retry_count": {
                        "type": "integer"
                    },
                    "error_code": {
                        "type": "keyword"
                    },
                    "duration_ms": {
                        "type": "integer"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "function": {
                                "type": "keyword"
                            },
                            "attempt": {
                                "type": "integer"
                            },
                            "error": {
                                "type": "text"
                            },
                            "job_id": {
                                "type": "keyword"
                            },
                            "peer_id": {
                                "type": "keyword"
                            },
                            "ack_status": {
                                "type": "keyword"
                            }
                        }
                    }
                }
            }
        }
    }
    
    try:
        # Create index template
        await elastic_handler.client.indices.put_index_template(
            name="telegram-monitoring-template",
            body=index_template
        )
        print("✅ Index template created successfully")
        
        # Create the actual index
        await elastic_handler.client.indices.create(
            index="telegram-monitoring",
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }
        )
        print("✅ Index 'telegram-monitoring' created successfully")
        
    except Exception as e:
        print(f"❌ Error setting up index: {e}")

if __name__ == "__main__":
    asyncio.run(setup_telegram_monitoring_index())
