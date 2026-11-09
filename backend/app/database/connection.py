"""
MongoDB connection helpers — async (Motor) and sync (PyMongo) clients.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database

from app.config import MONGODB_URI, DATABASE_NAME


# ── Async client (for FastAPI request handling) ──────────────────────
_async_client: AsyncIOMotorClient | None = None


def get_async_client() -> AsyncIOMotorClient:
    """Return a singleton async Motor client."""
    global _async_client
    if _async_client is None:
        _async_client = AsyncIOMotorClient(MONGODB_URI)
    return _async_client


def get_async_db() -> AsyncIOMotorDatabase:
    """Return the default async database handle."""
    return get_async_client()[DATABASE_NAME]


# ── Sync client (for scripts, seeding, index creation) ───────────────
_sync_client: MongoClient | None = None


def get_sync_client() -> MongoClient:
    """Return a singleton sync PyMongo client."""
    global _sync_client
    if _sync_client is None:
        _sync_client = MongoClient(MONGODB_URI)
    return _sync_client


def get_sync_db() -> Database:
    """Return the default sync database handle."""
    return get_sync_client()[DATABASE_NAME]

