"""Alembic environment.

Reads the database URL from ``VINDATA_API_DATABASE_URL`` (matches the API
settings). Migrations run synchronously via psycopg even though the API uses
the async driver — Alembic doesn't need async, and using the sync driver
keeps the migration code path simple.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from vindata_api.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Pull the URL from env; convert async driver to sync for Alembic.
url = os.environ.get(
    "VINDATA_API_DATABASE_URL",
    "postgresql+psycopg://vindata:vindata@postgres:5432/vindata",
).replace("+asyncpg", "+psycopg")
config.set_main_option("sqlalchemy.url", url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
