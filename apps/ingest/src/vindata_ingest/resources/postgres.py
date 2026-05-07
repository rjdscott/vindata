"""Synchronous SQLAlchemy session factory for Dagster ops.

Async engines don't play nicely with Dagster's threadpool execution model;
we use the sync ``psycopg`` driver here.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from dagster import ConfigurableResource
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class PostgresResource(ConfigurableResource):
    database_url: str
    pool_size: int = 5

    def _engine(self) -> Engine:
        return create_engine(
            self.database_url, pool_pre_ping=True, pool_size=self.pool_size, future=True
        )

    @contextmanager
    def session(self) -> Iterator[Session]:
        engine = self._engine()
        maker = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        with maker() as s:
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise
            finally:
                engine.dispose()
