"""
Elasticsearch queries for Telegram monitoring dashboard
"""

# 1. Account Status Overview
ACCOUNT_STATUS_QUERY = {
    "size": 0,
    "aggs": {
        "accounts": {
            "terms": {
                "field": "account_id.keyword",
                "size": 100
            },
            "aggs": {
                "latest_status": {
                    "top_hits": {
                        "sort": [{"timestamp": {"order": "desc"}}],
                        "size": 1,
                        "_source": ["status", "operation", "message", "timestamp"]
                    }
                },
                "status_counts": {
                    "terms": {
                        "field": "status.keyword"
                    }
                },
                "operation_counts": {
                    "terms": {
                        "field": "operation.keyword"
                    }
                }
            }
        }
    }
}

# 2. Channel Collection Statistics
CHANNEL_COLLECTION_STATS = {
    "size": 0,
    "aggs": {
        "channels": {
            "terms": {
                "field": "channel_username.keyword",
                "size": 50
            },
            "aggs": {
                "total_messages": {
                    "sum": {
                        "field": "message_count"
                    }
                },
                "collection_events": {
                    "value_count": {
                        "field": "message_count"
                    }
                },
                "latest_collection": {
                    "max": {
                        "field": "timestamp"
                    }
                }
            }
        }
    }
}

# 3. Error Analysis
ERROR_ANALYSIS_QUERY = {
    "query": {
        "bool": {
            "should": [
                {"term": {"level": "error"}},
                {"term": {"status": "banned"}},
                {"term": {"status": "rate_limited"}},
                {"term": {"status": "error"}}
            ]
        }
    },
    "size": 0,
    "aggs": {
        "error_types": {
            "terms": {
                "field": "error_code.keyword",
                "size": 20
            }
        },
        "error_by_account": {
            "terms": {
                "field": "account_id.keyword",
                "size": 10
            }
        },
        "error_timeline": {
            "date_histogram": {
                "field": "timestamp",
                "calendar_interval": "hour"
            }
        }
    }
}

# 4. Performance Metrics
PERFORMANCE_METRICS = {
    "size": 0,
    "aggs": {
        "avg_duration": {
            "avg": {
                "field": "duration_ms"
            }
        },
        "max_duration": {
            "max": {
                "field": "duration_ms"
            }
        },
        "duration_by_operation": {
            "terms": {
                "field": "operation.keyword"
            },
            "aggs": {
                "avg_duration": {
                    "avg": {
                        "field": "duration_ms"
                    }
                }
            }
        }
    }
}

# 5. Real-time Activity
REAL_TIME_ACTIVITY = {
    "query": {
        "range": {
            "timestamp": {
                "gte": "now-1h"
            }
        }
    },
    "sort": [{"timestamp": {"order": "desc"}}],
    "size": 100
}

# 6. Account Health Check
ACCOUNT_HEALTH_CHECK = {
    "query": {
        "bool": {
            "must": [
                {"range": {"timestamp": {"gte": "now-1h"}}}
            ]
        }
    },
    "size": 0,
    "aggs": {
        "accounts": {
            "terms": {
                "field": "account_id.keyword"
            },
            "aggs": {
                "last_activity": {
                    "max": {
                        "field": "timestamp"
                    }
                },
                "success_rate": {
                    "filters": {
                        "filters": {
                            "success": {"term": {"status": "connected"}},
                            "failed": {"term": {"status": "error"}}
                        }
                    }
                },
                "operations_count": {
                    "value_count": {
                        "field": "operation.keyword"
                    }
                }
            }
        }
    }
}

# 7. Message Collection Trends
MESSAGE_COLLECTION_TRENDS = {
    "query": {
        "bool": {
            "must": [
                {"term": {"operation": "message_collection"}},
                {"range": {"timestamp": {"gte": "now-24h"}}}
            ]
        }
    },
    "size": 0,
    "aggs": {
        "hourly_collection": {
            "date_histogram": {
                "field": "timestamp",
                "calendar_interval": "hour"
            },
            "aggs": {
                "total_messages": {
                    "sum": {
                        "field": "message_count"
                    }
                },
                "unique_channels": {
                    "cardinality": {
                        "field": "channel_id.keyword"
                    }
                }
            }
        }
    }
}

# 8. Retry Analysis
RETRY_ANALYSIS = {
    "query": {
        "term": {"operation": "retry"}
    },
    "size": 0,
    "aggs": {
        "retry_by_account": {
            "terms": {
                "field": "account_id.keyword"
            },
            "aggs": {
                "retry_count_distribution": {
                    "histogram": {
                        "field": "retry_count",
                        "interval": 1
                    }
                }
            }
        },
        "retry_reasons": {
            "terms": {
                "field": "metadata.error.keyword",
                "size": 20
            }
        }
    }
}
