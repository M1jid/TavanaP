import redis


class RedisWrapper:

    def __init__(self, redis_host, redis_port):
        self.client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    def store(self, key, value):
        self.client.set(key, value)

    def get(self, key):
        last_message_id = self.client.get(key)
        return last_message_id.decode('utf-8') if last_message_id else None
