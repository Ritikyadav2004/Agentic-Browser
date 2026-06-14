"""
FastAPI application entrypoint for the AI Shopping Agent backend.
"""
from __future__ import annotations

import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database.mongodb import close_mongo, init_indexes
from database.redis_client import close_redis
from routes import history, products
from services.browser_manager import browser_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting AI Shopping Agent backend...")

    await init_indexes()
    await browser_manager.start()

    yield

    logger.info("Shutting down AI Shopping Agent backend...")
    await browser_manager.stop()
    await close_mongo()
    await close_redis()


app = FastAPI(
    title="AI Shopping Agent API",
    description="Autonomous shopping recommendation agent powered by Claude, LangGraph, and Playwright.",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False if "*" in settings.cors_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api")
app.include_router(history.router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok", "service": "AI Shopping Agent API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
