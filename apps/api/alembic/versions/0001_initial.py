"""initial schema: vineyards, blocks, weather_forecasts, agronomy_scores.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensions are bootstrapped by infra/local/postgres/init.sql.
    # Re-asserting them here keeps the migration self-sufficient when applied
    # to a new (non-Docker-init) Postgres instance.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "vineyards",
        sa.Column("id", sa.SmallInteger, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("region", sa.String, nullable=False, server_default="Orange NSW"),
        sa.Column("centroid", Geography("POINT", srid=4326), nullable=False),
        sa.Column("tz", sa.String, nullable=False, server_default="Australia/Sydney"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "vineyard_id",
            sa.Integer,
            sa.ForeignKey("vineyards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("cultivar", sa.String),
        sa.Column("geom", Geography("POLYGON", srid=4326)),
        sa.Column("elevation_m", sa.Float),
        sa.Column("aspect_deg", sa.Float),
        sa.Column("slope_deg", sa.Float),
        sa.UniqueConstraint("vineyard_id", "name", name="uq_blocks_vineyard_name"),
    )

    op.create_table(
        "weather_forecasts",
        sa.Column("vineyard_id", sa.Integer, sa.ForeignKey("vineyards.id"), nullable=False),
        sa.Column("model", sa.String, nullable=False),
        sa.Column("init_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("t2m", sa.Float),
        sa.Column("dewpoint", sa.Float),
        sa.Column("rh", sa.Float),
        sa.Column("wind_ms", sa.Float),
        sa.Column("wind_dir", sa.Float),
        sa.Column("precip_mm", sa.Float),
        sa.Column("cloud_frac", sa.Float),
        sa.Column("sw_rad", sa.Float),
        sa.PrimaryKeyConstraint("vineyard_id", "model", "init_ts", "valid_ts"),
    )
    # Promote to a hypertable on valid_ts; 7-day chunks.
    op.execute(
        "SELECT create_hypertable('weather_forecasts', 'valid_ts', "
        "chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE)"
    )

    # `agronomy_scores` is *not* a TimescaleDB hypertable at PoC. Volumes are
    # tiny (~7 k rows/day) and TimescaleDB requires the PK to include the
    # partitioning column, which conflicts with our nullable ``block_id``
    # (vineyard-level scores). Plain table + surrogate BIGSERIAL PK + unique
    # constraint with NULLS NOT DISTINCT for the natural key gives us clean
    # upsert semantics without that constraint. We can convert to a
    # hypertable later when volumes justify it.
    op.create_table(
        "agronomy_scores",
        sa.Column(
            "id", sa.BigInteger, sa.Identity(always=False), primary_key=True
        ),
        sa.Column("vineyard_id", sa.Integer, sa.ForeignKey("vineyards.id"), nullable=False),
        sa.Column("block_id", sa.Integer, sa.ForeignKey("blocks.id")),
        sa.Column("wedge", sa.String, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lead_h", sa.SmallInteger, nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("level", sa.String, nullable=False),
        sa.Column("inputs", sa.JSON, nullable=False),
        sa.Column("model_version", sa.String, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "level IN ('low','elevated','high','extreme')",
            name="ck_agronomy_scores_level",
        ),
    )
    op.execute(
        "ALTER TABLE agronomy_scores ADD CONSTRAINT pk_agronomy_scores "
        "UNIQUE NULLS NOT DISTINCT (vineyard_id, wedge, ts, lead_h, block_id)"
    )
    op.create_index(
        "ix_agronomy_scores_vineyard_ts",
        "agronomy_scores",
        ["vineyard_id", "wedge", "ts"],
    )


def downgrade() -> None:
    op.drop_table("agronomy_scores")
    op.drop_table("weather_forecasts")
    op.drop_table("blocks")
    op.drop_table("vineyards")
