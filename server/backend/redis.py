import os
import redis.asyncio as redis

def generate_redis_url(num):
    return f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{num}"

def get_redis_client(num):
    return redis.from_url(generate_redis_url(num))

