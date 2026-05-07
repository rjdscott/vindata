"""SQLAlchemy ORM models.

All models share a single declarative ``Base`` so Alembic's ``autogenerate``
sees them in one metadata. Geometry columns use ``geoalchemy2``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Project-wide declarative base."""


class Vineyard(Base):
    __tablename__ = "vineyards"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str] = mapped_column(String, nullable=False, default="Orange NSW")
    centroid: Mapped[Any] = mapped_column(Geography("POINT", srid=4326), nullable=False)
    tz: Mapped[str] = mapped_column(String, nullable=False, default="Australia/Sydney")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    blocks: Mapped[list[Block]] = relationship(
        back_populates="vineyard", cascade="all, delete-orphan"
    )


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vineyard_id: Mapped[int] = mapped_column(
        ForeignKey("vineyards.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    cultivar: Mapped[str | None] = mapped_column(String)
    geom: Mapped[Any | None] = mapped_column(Geography("POLYGON", srid=4326))
    elevation_m: Mapped[float | None] = mapped_column(Float)
    aspect_deg: Mapped[float | None] = mapped_column(Float)
    slope_deg: Mapped[float | None] = mapped_column(Float)

    vineyard: Mapped[Vineyard] = relationship(back_populates="blocks")

    __table_args__ = (UniqueConstraint("vineyard_id", "name", name="uq_blocks_vineyard_name"),)


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    vineyard_id: Mapped[int] = mapped_column(
        ForeignKey("vineyards.id"), nullable=False
    )
    model: Mapped[str] = mapped_column(String, nullable=False)
    init_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    t2m: Mapped[float | None] = mapped_column(Float)
    dewpoint: Mapped[float | None] = mapped_column(Float)
    rh: Mapped[float | None] = mapped_column(Float)
    wind_ms: Mapped[float | None] = mapped_column(Float)
    wind_dir: Mapped[float | None] = mapped_column(Float)
    precip_mm: Mapped[float | None] = mapped_column(Float)
    cloud_frac: Mapped[float | None] = mapped_column(Float)
    sw_rad: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("vineyard_id", "model", "init_ts", "valid_ts"),
    )


class AgronomyScore(Base):
    __tablename__ = "agronomy_scores"

    # Surrogate key — Postgres forbids NULLs in PK columns and `block_id`
    # must stay nullable (vineyard-level scores). Uniqueness is enforced by
    # the `pk_agronomy_scores` UNIQUE NULLS NOT DISTINCT constraint defined
    # in the migration.
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    vineyard_id: Mapped[int] = mapped_column(ForeignKey("vineyards.id"), nullable=False)
    block_id: Mapped[int | None] = mapped_column(ForeignKey("blocks.id"))
    wedge: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lead_h: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "vineyard_id", "wedge", "ts", "lead_h", "block_id",
            name="pk_agronomy_scores",
        ),
        CheckConstraint(
            "level IN ('low','elevated','high','extreme')",
            name="ck_agronomy_scores_level",
        ),
    )


class PhenologyState(Base):
    __tablename__ = "phenology_state"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    block_id: Mapped[int] = mapped_column(
        ForeignKey("blocks.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    doy: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    chill_units: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    forcing_dd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gdd_from_budbreak: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bbch: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("block_id", "date", name="uq_phenology_state_block_date"),
        CheckConstraint("bbch BETWEEN 0 AND 99", name="ck_phenology_state_bbch_range"),
    )


class Pm25Observation(Base):
    __tablename__ = "pm25_observations"

    vineyard_id: Mapped[int] = mapped_column(
        ForeignKey("vineyards.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pm25_ug_m3: Mapped[float] = mapped_column(Float, nullable=False)
    station: Mapped[str] = mapped_column(String, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("vineyard_id", "ts"),
        CheckConstraint(
            "pm25_ug_m3 >= 0 AND pm25_ug_m3 < 5000",
            name="ck_pm25_observations_range",
        ),
    )


class FireHotspot(Base):
    __tablename__ = "fire_hotspots"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    geom: Mapped[Any] = mapped_column(Geography("POINT", srid=4326), nullable=False)
    brightness_k: Mapped[float | None] = mapped_column(Float)
    frp_mw: Mapped[float | None] = mapped_column(Float)
    satellite: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[int | None] = mapped_column(SmallInteger)
    source: Mapped[str] = mapped_column(String, nullable=False, default="firms_modis")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


__all__ = [
    "AgronomyScore",
    "Base",
    "Block",
    "FireHotspot",
    "PhenologyState",
    "Pm25Observation",
    "Vineyard",
    "WeatherForecast",
]
