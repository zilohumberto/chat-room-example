import redis
import logging
import pickle
import json
import aioredis


log = logging.getLogger(__name__)


class CacheGateway:
    redis_host = '0.0.0.0'
    redis_port = 6379
    redis_password = ""
    queue = None
    pool = None

    def __init__(self):
        self.queue = redis.StrictRedis(
            host=self.redis_host,
            port=self.redis_port,
            password="",
            decode_responses=True,
        )

    async def get_pool(self):
        self.pool = await aioredis.create_redis_pool(f'redis://{self.redis_host}:{self.redis_port}')

    async def subscribe(self, key):
        return await self.pool.subscribe(key)

    def publish_message(self, key, message):
        log.debug(f"publishing in {key}: {message}")
        return self.queue.publish(key, message)

    async def close(self):
        self.queue.close()
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    def get(self, key, is_json=False, is_pickle=False):
        value = self.queue.get(key)
        if is_json:
            return json.loads(value)
        if is_pickle:
            return pickle.loads(value)
        return value

    def set(self, key, value, is_json=False, is_pickle=False, expires=None):
        if is_json:
            formatted_value = json.dumps(value)
        elif is_pickle:
            formatted_value = pickle.dumps(value)
        else:
            formatted_value = value

        self.queue.set(key, formatted_value)
        if expires:
            self.queue.expire(key, expires)

    def delete(self, key):
        if self.queue.get(key):
            self.queue.delete(key)

    def lset(self, key, value):
        self.queue.lpush(key, value)

    def lget(self, key):
        _list = []
        if self.queue.llen(key) == 0:
            return _list
        while self.queue.llen(key) != 0:
            _list.append(self.queue.lpop(key))
        self.queue.lpush(key, *_list)
        return _list

