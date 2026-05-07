"""Vineyard / block response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Centroid(BaseModel):
    """GeoJSON-style point for the API surface (decoupled from PostGIS)."""

    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cultivar: str | None = None
    elevation_m: float | None = None
    aspect_deg: float | None = None
    slope_deg: float | None = None


class VineyardSummaryResponse(BaseModel):
    """Used in list views; omits blocks for payload size."""

    id: int
    slug: str
    name: str
    region: str
    centroid: Centroid


class VineyardDetailResponse(VineyardSummaryResponse):
    """Used in detail views; includes blocks."""

    blocks: list[BlockResponse]
