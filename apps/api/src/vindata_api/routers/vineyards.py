"""Vineyard endpoints.

Lon/lat are extracted in SQL via PostGIS ``ST_X`` / ``ST_Y`` rather than
parsing the WKB blob client-side, which avoids a hard shapely dependency
and keeps the API container slim.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from geoalchemy2 import Geometry
from sqlalchemy import func, select

from vindata_api.db import SessionDep
from vindata_api.models import Block, Vineyard
from vindata_api.schemas.vineyards import (
    BlockResponse,
    Centroid,
    VineyardDetailResponse,
    VineyardSummaryResponse,
)

router = APIRouter(prefix="/v1/vineyards", tags=["vineyards"])

# Cast geography → geometry once so ST_X / ST_Y can pull lon / lat out.
_centroid_geom = func.cast(Vineyard.centroid, Geometry)
_LON = func.ST_X(_centroid_geom).label("lon")
_LAT = func.ST_Y(_centroid_geom).label("lat")


@router.get("", response_model=list[VineyardSummaryResponse])
async def list_vineyards(session: SessionDep) -> list[VineyardSummaryResponse]:
    stmt = select(
        Vineyard.id, Vineyard.slug, Vineyard.name, Vineyard.region, _LAT, _LON
    ).order_by(Vineyard.id)
    return [
        VineyardSummaryResponse(
            id=row.id,
            slug=row.slug,
            name=row.name,
            region=row.region,
            centroid=Centroid(lat=float(row.lat), lon=float(row.lon)),
        )
        for row in (await session.execute(stmt))
    ]


@router.get("/{vineyard_id}", response_model=VineyardDetailResponse)
async def get_vineyard(vineyard_id: int, session: SessionDep) -> VineyardDetailResponse:
    stmt = select(
        Vineyard.id, Vineyard.slug, Vineyard.name, Vineyard.region, _LAT, _LON
    ).where(Vineyard.id == vineyard_id)
    row = (await session.execute(stmt)).one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vineyard not found")

    blocks_q = await session.execute(
        select(Block).where(Block.vineyard_id == vineyard_id).order_by(Block.id)
    )
    return VineyardDetailResponse(
        id=row.id,
        slug=row.slug,
        name=row.name,
        region=row.region,
        centroid=Centroid(lat=float(row.lat), lon=float(row.lon)),
        blocks=[BlockResponse.model_validate(b) for b in blocks_q.scalars().all()],
    )
