from elasticsearch import Elasticsearch
from kafka_router import KafkaRouter

# ---------- Elasticsearch ----------
ES_HOST = "https://192.168.10.60:9200"
ES_USER = "elastic"
ES_PASS = "change-me"
INDEX_NAME = "instagram_post_v4"
MAPPING = {
  "mappings": {
    "properties": {
      "post": {
        "properties": {
          "id": {"type": "keyword"},
          "url": {"type": "keyword"},
          "caption": {"type": "text"},
          "clear_caption": {"type": "text"},
          "taken_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
          "like_count": {"type": "long"},
          "comment_count": {"type": "long"},
          "is_video": {"type": "boolean"},
          "final_photo_url": {"type": "keyword"},
          "thumbnails": {"type": "keyword"},
          "hashtags": {"type": "keyword"},
          "mentions": {"type": "keyword"},
          "location": {"type": "keyword"}
        }
      },
      "owner": {
        "properties": {
          "username": {"type": "keyword"},
          "owner_id": {"type": "keyword"},
          "owner_profile_pic_url": {"type": "keyword"}
        }
      },
      "analysis": {
        "properties": {
          "SENSE": {"type": "keyword"},
          "TAGS": {"type": "keyword"},
          "SENTIMENT": {"type": "keyword"}
        }
      },
      "comments": {
        "type": "nested",
        "properties": {
          "username": {"type": "keyword"},
          "comment": {"type": "text"},
          "likes": {"type": "long"},
          "created_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
          "profile_pic_url": {"type": "keyword"},
          "replies": {
            "type": "nested",
            "properties": {
              "username": {"type": "keyword"},
              "comment": {"type": "text"},
              "likes": {"type": "long"},
              "created_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
              "profile_pic_url": {"type": "keyword"}
            }
          }
        }
      },
      "raw_node": {"type": "object", "enabled": True}
    }
  }
}




es = Elasticsearch(ES_HOST, basic_auth=(ES_USER, ES_PASS), verify_certs=False)

# ---------- Instagram ----------
INSTAGRAM_USERNAME = "mahdid580"
INSTAGRAM_PASSWORD = "MMMmmm@123"
SESSION_STATE = "session.json"

# ---------- Kafka ----------
KAFKA_BOOTSTRAP_SERVERS = '192.168.10.60:9092'
ROUTING_ROLES = 'routing_rules.json'
kafka_router = KafkaRouter(kafka_host=KAFKA_BOOTSTRAP_SERVERS, config_path=ROUTING_ROLES)

# ---------- Files ----------
USERS_FILE = "shared/updated_users.txt"
STATE_FILE = "last_posts.json"
DATA_FILE = "new_posts_output.json"
