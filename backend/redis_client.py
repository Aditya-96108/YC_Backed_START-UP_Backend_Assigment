import os
import redis.asyncio as redis
from kombu.utils.url import safequote

redis_host = safequote(os.environ.get("REDIS_HOST", "localhost"))
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

async def add_key_value_redis(key: str, value: str, expire: int | None = None) -> None:
    """
    Stores a key-value pair in Redis with an optional expiry time.
    Args:
        key: The Redis key.
        value: The value to store.
        expire: Expiry time in seconds, if applicable.
    """
    await redis_client.set(key, value)
    if expire:
        await redis_client.expire(key, expire)

async def get_value_redis(key: str) -> bytes | None:
    """
    Retrieves a value from Redis by key.
    Args:
        key: The Redis key.
    Returns:
        The value as bytes, or None if the key does not exist.
    """
    return await redis_client.get(key)

async def delete_key_redis(key: str) -> None:
    """
    Deletes a key from Redis.
    Args:
        key: The Redis key.
    """
    await redis_client.delete(key)
