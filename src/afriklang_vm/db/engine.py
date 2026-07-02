"""Async SQLAlchemy engine, session factory, and schema initialization.

Uses SQLite + FTS5 for the hackathon demo. The FTS5 virtual table
``voice_messages_fts`` mirrors ``voice_messages.transcribed_text`` and is kept
in sync via triggers, enabling fast full-text search over transcriptions.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from afriklang_vm.domain.models import Base

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None

# FTS5 virtual table + triggers keeping it in sync with voice_messages.
_FTS_STATEMENTS: tuple[str, ...] = (
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS voice_messages_fts
    USING fts5(transcribed_text, content='voice_messages', content_rowid='id');
    """,
    """
    CREATE TRIGGER IF NOT EXISTS voice_messages_ai AFTER INSERT ON voice_messages BEGIN
        INSERT INTO voice_messages_fts(rowid, transcribed_text)
        VALUES (new.id, new.transcribed_text);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS voice_messages_ad AFTER DELETE ON voice_messages BEGIN
        INSERT INTO voice_messages_fts(voice_messages_fts, rowid, transcribed_text)
        VALUES('delete', old.id, old.transcribed_text);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS voice_messages_au AFTER UPDATE ON voice_messages BEGIN
        INSERT INTO voice_messages_fts(voice_messages_fts, rowid, transcribed_text)
        VALUES('delete', old.id, old.transcribed_text);
        INSERT INTO voice_messages_fts(rowid, transcribed_text)
        VALUES (new.id, new.transcribed_text);
    END;
    """,
)


def _ensure_sqlite_dir(database_url: str) -> None:
    """Create the parent directory for a file-based SQLite database."""
    marker = ":///"
    if "sqlite" in database_url and marker in database_url:
        path = database_url.split(marker, 1)[1]
        if path and path != ":memory:":
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)


def init_engine(database_url: str) -> AsyncEngine:
    """Create (once) and return the global async engine."""
    global _engine, _sessionmaker
    if _engine is None:
        _ensure_sqlite_dir(database_url)
        _engine = create_async_engine(database_url, future=True, echo=False)
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the configured session factory."""
    if _sessionmaker is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional session scope."""
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables and the FTS5 search index."""
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for statement in _FTS_STATEMENTS:
            await conn.execute(text(statement))


async def dispose_engine() -> None:
    """Dispose the engine (shutdown)."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
