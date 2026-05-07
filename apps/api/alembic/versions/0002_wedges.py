"""wedges: phenology_state, pm25_observations, fire_hotspots, wedge check.

Revision ID: 0002_wedges
Revises: 0001_initial
Create Date: 2026-05-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision: str = "0002_wedges"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Per-block daily phenology state. The disease and smoke wedges read
    # ``bbch`` from the latest row to gate their scores. Surrogate PK +
    # uniqueness on (block_id, date) for clean upsert; no Timescale on
    # this table — daily volume is tiny and we'd rather keep it simple.
    op.create_table(
        "phenology_state",
        sa.Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
        sa.Column(
            "block_id",
            sa.Integer,
            sa.ForeignKey("blocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("doy", sa.SmallInteger, nullable=False),
        sa.Column("chill_units", sa.Float, nullable=False, server_default="0"),
        sa.Column("forcing_dd", sa.Float, nullable=False, server_default="0"),
        sa.Column("gdd_from_budbreak", sa.Float, nullable=False, server_default="0"),
        sa.Column("bbch", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("model_version", sa.String, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("block_id", "date", name="uq_phenology_state_block_date"),
        sa.CheckConstraint("bbch BETWEEN 0 AND 99", name="ck_phenology_state_bbch_range"),
    )
    op.create_index(
        "ix_phenology_state_block_date_desc",
        "phenology_state",
        ["block_id", sa.text("date DESC")],
    )

    # Per-vineyard PM2.5 observations from NSW DPE AirQuality. Hypertable
    # on ts because volume is meaningful (~96 rows/day/vineyard at 15 min
    # cadence) and time-bucketed reads dominate.
    op.create_table(
        "pm25_observations",
        sa.Column(
            "vineyard_id",
            sa.Integer,
            sa.ForeignKey("vineyards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pm25_ug_m3", sa.Float, nullable=False),
        sa.Column("station", sa.String, nullable=False),
        sa.Column("distance_km", sa.Float, nullable=False),
        sa.PrimaryKeyConstraint("vineyard_id", "ts"),
        sa.CheckConstraint(
            "pm25_ug_m3 >= 0 AND pm25_ug_m3 < 5000",
            name="ck_pm25_observations_range",
        ),
    )
    op.execute(
        "SELECT create_hypertable('pm25_observations', 'ts', "
        "chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE)"
    )

    # Geographic fire hotspots from NASA FIRMS. Not per-vineyard — the
    # scoring asset queries by ST_DWithin on the geography column. Plain
    # table; volumes are tiny (a quiet day has 0 hotspots).
    op.create_table(
        "fire_hotspots",
        sa.Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("geom", Geography("POINT", srid=4326), nullable=False),
        sa.Column("brightness_k", sa.Float),
        sa.Column("frp_mw", sa.Float),
        sa.Column("satellite", sa.String, nullable=False),
        sa.Column("confidence", sa.SmallInteger),
        sa.Column("source", sa.String, nullable=False, server_default="firms_modis"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # No natural unique key — FIRMS detection IDs aren't stable across
        # daily reprocessing; we treat each ingest as additive and dedupe
        # in the scoring window.
    )
    op.create_index("ix_fire_hotspots_ts", "fire_hotspots", ["ts"])
    op.create_index(
        "ix_fire_hotspots_geom",
        "fire_hotspots",
        ["geom"],
        postgresql_using="gist",
    )

    # Constrain the wedge column on agronomy_scores. We've allowed
    # arbitrary strings until now — tighten as the surface stabilises.
    op.create_check_constraint(
        "ck_agronomy_scores_wedge",
        "agronomy_scores",
        "wedge IN ('frost','dm','pm','botrytis','smoke','pheno')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_agronomy_scores_wedge", "agronomy_scores", type_="check")
    op.drop_index("ix_fire_hotspots_geom", table_name="fire_hotspots")
    op.drop_index("ix_fire_hotspots_ts", table_name="fire_hotspots")
    op.drop_table("fire_hotspots")
    op.drop_table("pm25_observations")
    op.drop_index("ix_phenology_state_block_date_desc", table_name="phenology_state")
    op.drop_table("phenology_state")
