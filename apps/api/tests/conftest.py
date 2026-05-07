"""Shared pytest fixtures.

Integration tests are tagged with ``@pytest.mark.integration`` and assume
the local docker-compose stack is up (``make up``). They reach the live
``vindata`` Postgres on ``localhost:5432`` via the ``VINDATA_TEST_DATABASE_URL``
environment variable, defaulting to the docker-compose default credentials.

Each integration test runs inside a SAVEPOINT and is rolled back on teardown,
so tests don't leak state across each other or contaminate the dev DB.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from vindata_api.db import get_db_session
from vindata_api.main import create_app
from vindata_api.settings import Settings

_DEFAULT_TEST_URL = "postgresql+asyncpg://vindata:vindata@localhost:5432/vindata"


def _test_database_url() -> str:
    return os.environ.get("VINDATA_TEST_DATABASE_URL", _DEFAULT_TEST_URL)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Yield a session bound to a transaction that is rolled back on teardown.

    Each test sees a clean slate even though we're sharing the dev DB.
    """
    engine = create_async_engine(_test_database_url(), pool_pre_ping=True)
    connection = await engine.connect()
    transaction = await connection.begin()
    sessionmaker = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = sessionmaker()
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncIterator[AsyncClient]:
    """Async HTTP client wired to the FastAPI app with the session override."""
    app = create_app(Settings(_env_file=None, database_url=_test_database_url()))

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip @integration tests unless the user opts in.

    Run with ``pytest -m integration`` to include them; default ``pytest`` skips.
    """
    if config.getoption("-m"):
        return
    skip_integration = pytest.mark.skip(reason="run with `pytest -m integration`")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
