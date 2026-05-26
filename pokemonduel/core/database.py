"""
pokemonduel.core.database
=========================
Async MongoDB connection pool manager using Motor.

Reads ``MONGO_URI`` from environment variables (loaded via python-dotenv).
Provides a singleton connection lifecycle: connect once at bot startup,
access the database instance anywhere, close on shutdown.

Security: Connection strings are never hardcoded.  The module refuses
to connect if ``MONGO_URI`` is not set.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

log = logging.getLogger("dueler.database")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

# Default database name — override by setting MONGO_DB_NAME in .env
_DEFAULT_DB_NAME = "pokemonduel"


async def connect() -> AsyncIOMotorDatabase:
    """
    Establish the MongoDB connection and return the database handle.

    Call this once during bot startup (``setup_hook``).  Subsequent calls
    return the same cached connection.

    Raises
    ------
    RuntimeError
        If ``MONGO_URI`` is not set in the environment.
    """
    global _client, _db
    if _db is not None:
        return _db

    uri = os.environ.get("MONGO_URI")
    if not uri:
        raise RuntimeError(
            "MONGO_URI environment variable is not set.  "
            "Add it to your .env file (see .env.example)."
        )

    db_name = os.environ.get("MONGO_DB_NAME", _DEFAULT_DB_NAME)

    # Motor's AsyncIOMotorClient pools connections internally.
    # serverSelectionTimeoutMS prevents hanging on unreachable clusters.
    _client = AsyncIOMotorClient(
        uri,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=10_000,
        maxPoolSize=50,
        minPoolSize=5,
        retryWrites=True,
        retryReads=True,
    )

    _db = _client[db_name]

    # Ping to verify connectivity at startup rather than failing later.
    await _client.admin.command("ping")
    log.info("MongoDB connected — database=%r", db_name)
    return _db


def get_db() -> AsyncIOMotorDatabase:
    """
    Return the active database handle.

    Raises ``RuntimeError`` if :func:`connect` has not been called yet.
    """
    if _db is None:
        raise RuntimeError("Database not initialised — call connect() first.")
    return _db


async def close() -> None:
    """Gracefully close the MongoDB connection pool."""
    global _client, _db
    if _client is not None:
        _client.close()
        log.info("MongoDB connection closed.")
        _client = None
        _db = None


async def health_check() -> bool:
    """Return ``True`` if the database is reachable."""
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False
