"""
Elasticsearch configuration definitions for the Telegram application.

This module contains Elasticsearch index definitions with mappings and settings.
"""

from app.core.config import settings

# Elasticsearch Index Definitions
ELASTICSEARCH_INDEX_DEFINITIONS = [
  {
    "name": f"{settings.TELEGRAM_MESSAGES_TOPIC_NAME}",
    "config": {
        f"{settings.TELEGRAM_MESSAGES_TOPIC_NAME}" : {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 2
            },
            "mappings" : {
                "properties" : {
                    "ID" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "PRIVATE_URL" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "PUBLIC_URL" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "PEER_ID" : {
                        "type" : "long"
                    },
                    "PEER_TYPE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "MESSAGE_ID" : {
                        "type" : "long"
                    },
                    "TYPE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "FETCH_TIME" : {
                        "type" : "long"
                    },
                    "DATE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "REPLY_PEER_ID" : {
                        "type" : "long"
                    },
                    "REPLY_LINK" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "REPLY_PEER_TYPE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "FWD_PEER_ID" : {
                        "type" : "long"
                    },
                    "FWD_LINK" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "FWD_PEER_TYPE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "AUTHOR_ID" : {
                        "type" : "long"
                    },
                    "AUTHOR_TYPE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "SENTIMENT" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "SENSE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "TAGS" : {
                        "type" : "keyword"
                    },
                    "VIEWS_COUNT" : {
                        "type" : "long"
                    },
                    "FORWARDS_COUNT" : {
                        "type" : "long"
                    },
                    "REACTIONS_COUNT" : {
                        "type" : "long"
                    },
                    "REPLIES_COUNT" : {
                        "type" : "long"
                    },
                    "CLEANED_MESSAGE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "REACTIONS" : {
                        "type" : "nested",
                        "properties" : {
                            "EMOJI" : {
                                "type" : "text",
                                "fields" : {
                                    "keyword" : {
                                        "type" : "keyword"
                                    }
                                }
                            },
                            "COUNT" : {
                                "type" : "long"
                            }
                        }
                    },
                    "MESSAGE" : {
                        "type" : "text",
                        "fields" : {
                            "keyword" : {
                                "type" : "keyword"
                            }
                        }
                    },
                    "MEDIA" : {
                        "type" : "keyword"
                    },
                    "LINKS" : {
                        "type" : "keyword"
                    },
                    "MENTIONS" : {
                        "type" : "keyword"
                    },
                    "HASHTAGS" : {
                        "type" : "keyword"
                    },
                    "BOLDED_PARTS" : {
                        "type" : "keyword"
                    },
                    "STRIKETHROUGHT_PARTS" : {
                        "type" : "keyword"
                    },
                    "MONOSPACE_PARTS" : {
                        "type" : "keyword"
                    },
                    "SPOILER_PARTS" : {
                        "type" : "keyword"
                    },
                    "BLOCKQUOTE_PARTS" : {
                        "type" : "keyword"
                    },
                    "STRIKETHROUGHED_PARTS" : {
                        "type" : "keyword"
                    },
                    "CODES" : {
                        "type" : "keyword"
                    }
                }
            }
        }  
    }
  },
  {
    "name": f"{settings.TELEGRAM_USERS_TOPIC_NAME}",
    "config": {
      f"{settings.TELEGRAM_USERS_TOPIC_NAME}" : {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 2
        },
        "mappings" : {
          "properties" : {
            "ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "USER_ID" : {
              "type" : "long"
            },
            "FETCH_TIME" : {
              "type" : "long"
            },
            "USERNAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "PHONE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "FIRST_NAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "LAST_NAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "BIO" : {
              "type" : "text"
            },
            "PRIVATE_FORWARD_NAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "BIRTHDAY" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "PERSONAL_CHANNEL_ID" : {
              "type" : "long"
            },
            "PERSONAL_CHANNEL_TITLE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            }
          }
        }
      }  
    }
  },
  {
    "name": f"{settings.TELEGRAM_BOTS_TOPIC_NAME}",
    "config": {
      f"{settings.TELEGRAM_BOTS_TOPIC_NAME}" : {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 2
        },
        "mappings" : {
          "properties" : {
            "ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "FETCH_TIME" : {
              "type" : "long"
            },
            "USERNAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "PHONE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "FIRST_NAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "LAST_NAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "BIO" : {
              "type" : "text"
            },
            "PRIVATE_FORWARD_NAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "BIRTHDAY" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "PERSONAL_CHANNEL_ID" : {
              "type" : "long"
            },
            "PERSONAL_CHANNEL_TITLE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "URL" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            }
          }
        }
      }  
    }
  },
  {
    "name": f"{settings.TELEGRAM_CHANNELS_TOPIC_NAME}",
    "config": {
      f"{settings.TELEGRAM_CHANNELS_TOPIC_NAME}" : {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 2
        },
        "mappings" : {
          "properties" : {
            "ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "FETCH_TIME" : {
              "type" : "long"
            },
            "TYPE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "PEER_ID" : {
              "type" : "long"
            },
            "USERNAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "TITLE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "DESCRIPTION" : {
              "type" : "text"
            },
            "URL" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "FOLLOWERS" : {
              "type" : "nested",
              "properties" : {
                "FOLLOWERS" : {
                  "type" : "long"
                },
                "FETCH_TIME" : {
                  "type" : "text",
                  "fields" : {
                    "keyword" : {
                      "type" : "keyword"
                    }
                  }
                }
              }
            },
            "TAG" : {
              "type" : "keyword"
            },
            "LINKED_GROUP_TITLE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "LINKED_GROUP_USERNAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "LINKED_GROUP_ID" : {
              "type" : "long"
            },
            "AVAILABLE_REACTIONS" : {
              "type" : "keyword"
            },
            "CAN_VIEW_PARTICIPANTS" : {
              "type" : "boolean"
            }
          }
        }
      }  
    }
  },
  {
    "name": f"{settings.TELEGRAM_GROUPS_TOPIC_NAME}",
    "config": {
      f"{settings.TELEGRAM_GROUPS_TOPIC_NAME}" : {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 2
        },
        "mappings" : {
          "properties" : {
            "ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "PEER_ID" : {
              "type" : "long"
            },
            "FETCH_TIME" : {
              "type" : "long"
            },
            "USERNAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "URL" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "TITLE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "DESCRIPTION" : {
              "type" : "text"
            },
            "AVAILABLE_REACTIONS" : {
              "type" : "keyword"
            },
            "FOLLOWERS" : {
              "type" : "nested",
              "properties" : {
                "FOLLOWERS" : {
                  "type" : "long"
                },
                "FETCH_TIME" : {
                  "type" : "text",
                  "fields" : {
                    "keyword" : {
                      "type" : "keyword"
                    }
                  }
                }
              }
            },
            "TAG" : {
              "type" : "keyword"
            },
            "CAN_VIEW_PARTICIPANTS" : {
              "type" : "boolean"
            },
            "LINKED_CHANNEL_ID" : {
              "type" : "long"
            },
            "LINKED_CHANNEL_TITLE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "LINKED_CHANNEL_USERNAME" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            }
          }
        }
      }
    }
  },
  {
    "name": f"{settings.TELEGRAM_CHATS_TOPIC_NAME}",
    "config": {
      f"{settings.TELEGRAM_CHATS_TOPIC_NAME}" : {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 2
        },
        "mappings" : {
          "properties" : {
            "ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "MEDIA" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "GROUPED_ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "OUT" : {
              "type" : "boolean"
            },
            "ADMIN_PEER_ID" : {
              "type" : "long"
            },
            "FETCH_TIME" : {
              "type" : "long"
            },
            "DATE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "EDIT_DATE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "TYPE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "AUTHOR_ID" : {
              "type" : "long"
            },
            "AUTHOR_TYPE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "PEER_ID" : {
              "type" : "long"
            },
            "PEER_TYPE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "URL" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "MESSAGE_ID" : {
              "type" : "long"
            },
            "MESSAGE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "REPLY_PEER_TYPE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "REPLY_PEER_ID" : {
              "type" : "long"
            },
            "REPLY_LINK" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "FWD_PEER_TYPE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "FWD_PEER_ID" : {
              "type" : "long"
            },
            "TEXT_REACTIONS" : {
              "type" : "keyword"
            },
            "TAGS" : {
              "type" : "keyword"
            },
            "SENTIMENT" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "SENSE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "CLEANED_MESSAGE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "LINKS" : {
              "type" : "keyword"
            },
            "MENTIONS" : {
              "type" : "keyword"
            },
            "HASHTAGS" : {
              "type" : "keyword"
            },
            "BOLDED_PARTS" : {
              "type" : "keyword"
            },
            "STRIKETHROUGHT_PARTS" : {
              "type" : "keyword"
            },
            "MONOSPACE_PARTS" : {
              "type" : "keyword"
            },
            "SPOILER_PARTS" : {
              "type" : "keyword"
            },
            "BLOCKQUOTE_PARTS" : {
              "type" : "keyword"
            },
            "STRIKETHROUGHED_PARTS" : {
              "type" : "keyword"
            },
            "CODES" : {
              "type" : "keyword"
            }
          }
        }
      }  
    }
  },
  {
    "name": f"{settings.TELEGRAM_TEST_TOPIC_NAME}",
    "config": {
      f"{settings.TELEGRAM_TEST_TOPIC_NAME}" : {
        "settings": {
          "number_of_shards": 3,
          "number_of_replicas": 2
        },
        "mappings" : {
          "properties" : {
            "ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "MESSAGE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            }
          }
        }
      }
    }
  },
  {
    "name": f"{settings.TELEGRAM_TEST2_TOPIC_NAME}",
    "config": {
      f"{settings.TELEGRAM_TEST2_TOPIC_NAME}" : {
        "settings": {
          "number_of_shards": 3,
          "number_of_replicas": 2
        },
        "mappings" : {
          "properties" : {
            "ID" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            },
            "MESSAGE" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword"
                }
              }
            }
          }
        }
      }
    }
  }
]

__all__ = ["ELASTICSEARCH_INDEX_DEFINITIONS"]
