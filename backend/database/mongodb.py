"""
MongoDB connection management using Motor (async driver).
"""
from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        settings = get_settings()
        _db = get_mongo_client()[settings.mongo_db_name]
    return _db


async def init_indexes() -> None:
    """Create indexes required by the application. Safe to call repeatedly."""
    db = get_db()
    try:
        await db.products.create_index([("source", 1), ("title", 1)])
        await db.products.create_index("scraped_at")
        await db.search_history.create_index([("user_id", 1), ("created_at", -1)])
        await db.search_history.create_index("session_id", unique=True)
        await db.recommendations.create_index("session_id")
        await db.recommendations.create_index("created_at")
        logger.info("MongoDB indexes ensured.")
    except Exception:
        logger.exception("Failed to create MongoDB indexes")


async def close_mongo() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
    _db = None
