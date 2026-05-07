"""Idempotent seed for the 6-vineyard pilot around Mount Canobolas.

The other 5 vineyard names + coordinates are placeholders; the Stage 00 doc
records that the user will confirm them before Stage 01. We use realistic
nearby points (within ~10 km of Cargo Road) so the map looks credible.

Cargo Road Vineyard: -33.317, 148.957  (anchor)
Mount Canobolas peak: -33.336, 149.013

Each vineyard now seeds at least one block with a cultivar so the
phenology / disease / smoke wedges have something to score per-block.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from vindata_api.db import init_db
from vindata_api.logging_config import configure_logging
from vindata_api.models import Block, Vineyard
from vindata_api.settings import get_settings

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _SeedBlock:
    """Block parameters seeded for each pilot vineyard.

    Defaults reflect typical Orange basalt/granite terraces: 4° slope,
    180° (north-facing in SH = sun-facing) aspect, 950 m elevation. The
    cultivar drives Caffarra-Eccel parameter selection downstream.
    """

    name: str
    cultivar: str
    elevation_m: float = 950.0
    aspect_deg: float = 180.0
    slope_deg: float = 4.0


@dataclass(frozen=True, slots=True)
class _SeedVineyard:
    slug: str
    name: str
    lat: float
    lon: float
    blocks: tuple[_SeedBlock, ...]


PILOT_VINEYARDS: tuple[_SeedVineyard, ...] = (
    _SeedVineyard(
        "cargo-road",
        "Cargo Road Wines",
        -33.317,
        148.957,
        blocks=(
            _SeedBlock("Block 1 — Chardonnay", "Chardonnay", elevation_m=950.0, slope_deg=4.0),
            _SeedBlock("Block 2 — Shiraz", "Shiraz", elevation_m=940.0, slope_deg=6.0),
        ),
    ),
    # Five placeholders within ~10 km of Cargo Road.
    _SeedVineyard(
        "placeholder-2", "Vineyard 2 (TBC)", -33.330, 148.985,
        blocks=(_SeedBlock("Block 1", "Chardonnay"),),
    ),
    _SeedVineyard(
        "placeholder-3", "Vineyard 3 (TBC)", -33.300, 148.940,
        blocks=(_SeedBlock("Block 1", "Pinot Noir"),),
    ),
    _SeedVineyard(
        "placeholder-4", "Vineyard 4 (TBC)", -33.350, 148.970,
        blocks=(_SeedBlock("Block 1", "Shiraz"),),
    ),
    _SeedVineyard(
        "placeholder-5", "Vineyard 5 (TBC)", -33.320, 149.020,
        blocks=(_SeedBlock("Block 1", "Chardonnay"),),
    ),
    _SeedVineyard(
        "placeholder-6", "Vineyard 6 (TBC)", -33.290, 148.990,
        blocks=(_SeedBlock("Block 1", "Pinot Noir"),),
    ),
)


async def seed() -> None:
    configure_logging("info")
    settings = get_settings()
    db = init_db(settings)

    async with db._sessionmaker() as session:
        for v in PILOT_VINEYARDS:
            stmt = (
                pg_insert(Vineyard)
                .values(
                    slug=v.slug,
                    name=v.name,
                    region="Orange NSW",
                    centroid=f"SRID=4326;POINT({v.lon} {v.lat})",
                    tz="Australia/Sydney",
                )
                .on_conflict_do_nothing(index_elements=["slug"])
            )
            await session.execute(stmt)

        # Seed blocks for every vineyard, idempotent on (vineyard_id, name).
        n_blocks = 0
        for v in PILOT_VINEYARDS:
            result = await session.execute(
                select(Vineyard).where(Vineyard.slug == v.slug)
            )
            vineyard = result.scalar_one()
            for b in v.blocks:
                existing = await session.execute(
                    select(Block).where(
                        Block.vineyard_id == vineyard.id, Block.name == b.name
                    )
                )
                if existing.scalar_one_or_none() is None:
                    session.add(
                        Block(
                            vineyard_id=vineyard.id,
                            name=b.name,
                            cultivar=b.cultivar,
                            elevation_m=b.elevation_m,
                            aspect_deg=b.aspect_deg,
                            slope_deg=b.slope_deg,
                        )
                    )
                    n_blocks += 1

        await session.commit()
        log.info(
            "seed.complete",
            vineyards=len(PILOT_VINEYARDS),
            blocks_inserted=n_blocks,
        )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
