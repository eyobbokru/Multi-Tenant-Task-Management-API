# app/db/redis.py
from redis import Redis
from functools import lru_cache
from app.core.config import settings

@lru_cache()
def get_redis() -> Redis:
    """
    Create a Redis connection pool and return a client.
    Uses lru_cache to maintain a single instance.
    """
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )
    return redis_client