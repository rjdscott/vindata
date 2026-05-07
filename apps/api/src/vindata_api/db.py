"""SQLAlchemy 2.0 async engine + session factory.

The engine is constructed lazily so tests can override settings before the
first session is opened. ``get_session`` is the FastAPI dependency.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from vindata_api.settings import Settings, get_settings


class Database:
    """Engine + session-maker bundle. One per process."""

    def __init__(self, settings: Settings) -> None:
        self._engine: AsyncEngine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            future=True,
        )
        self._sessionmaker = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessionmaker() as session:
            yield session

    async def dispose(self) -> None:
        await self._engine.dispose()


_db: Database | None = None


def init_db(settings: Settings) -> Database:
    global _db  # noqa: PLW0603
    _db = Database(settings)
    return _db


async def shutdown_db() -> None:
    global _db  # noqa: PLW0603
    if _db is not None:
        await _db.dispose()
        _db = None


async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a fresh ``AsyncSession`` per request."""
    if _db is None:
        init_db(settings)
    assert _db is not None
    async for session in _db.session():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
