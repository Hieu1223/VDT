"""Shared async Redis client (singleton).

Both presence tracking and ticket locks now live in Redis rather than in
process memory or in the Mongo document - this keeps state consistent across
multiple backend instances (horizontal scale-out) and lets TTL/expiry be
handled natively by Redis rather than by periodic sweep jobs.
"""
import logging

import redis.asyncio as redis

from common.config import settings

logger = logging.getLogger("redis")

# Single shared connection pool - lazily created on first use (and
# re-connected during gateway lifespan). All modules import `redis_client`
# from here rather than constructing their own client.
_client: redis.Redis | None = None


async def connect() -> redis.Redis:
    """Create (or reuse) the global async Redis connection pool."""
    global _client
    if _client is None:
        _client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=64,
        )
    # Ping so startup fails fast (and loudly) if Redis is unreachable.
    await _client.ping()
    logger.info("Redis connected: %s", settings.redis_url)
    return _client


async def disconnect() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Redis disconnected")


def get_redis() -> redis.Redis:
    """Returns the connected client. Must be called after `connect()`."""
    if _client is None:
        raise RuntimeError("Redis not initialised - call connect() first")
    return _client


# Convenience handle. Modules do `from common.redis_client import redis_client`
# and `await redis_client.<cmd>(...)`. It is bound to the live pool after
# connect(); before connect it is None.
redis_client: redis.Redis | None = _client


def _bind(client: redis.Redis) -> None:
    """Rebind the module-level `redis_client` handle to the live pool."""
    global redis_client
    redis_client = client


async def init() -> redis.Redis:
    """Connect + bind the module-level handle. Called from gateway lifespan."""
    client = await connect()
    _bind(client)
    return client
