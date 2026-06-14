"""
Redis cache client and helper functions for caching scraped/search results.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from config import get_settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    try:
        client = get_redis()
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.exception("Redis GET failed for key=%s", key)
        return None


async def cache_set(key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
    try:
        client = get_redis()
        settings = get_settings()
        ttl = ttl_seconds if ttl_seconds is not None else settings.redis_ttl_seconds
        await client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        logger.exception("Redis SET failed for key=%s", key)


async def cache_delete(key: str) -> None:
    try:
        client = get_redis()
        await client.delete(key)
    except Exception:
        logger.exception("Redis DELETE failed for key=%s", key)


def build_search_cache_key(category: str, budget: Optional[float], purpose: Optional[str]) -> str:
    return f"search:{category}:{budget}:{purpose}".lower().replace(" ", "_")


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
    logger.info("Redis client closed.")
