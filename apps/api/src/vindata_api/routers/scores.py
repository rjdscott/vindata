"""Agronomy score endpoints.

Stage 00 ships only the frost wedge. Other wedges are accepted by the query
parameter but return empty arrays until Stage 01.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import select

from vindata_api.db import SessionDep
from vindata_api.models import AgronomyScore, WeatherForecast
from vindata_api.schemas.scores import ScoreResponse, WedgeLiteral

router = APIRouter(prefix="/v1/vineyards/{vineyard_id}", tags=["scores"])


@router.get("/scores", response_model=list[ScoreResponse])
async def get_scores(
    vineyard_id: int,
    session: SessionDep,
    wedge: WedgeLiteral = Query("frost"),
    hours: int = Query(72, ge=1, le=240),
) -> list[ScoreResponse]:
    cutoff = datetime.now(tz=UTC) - timedelta(hours=6)
    horizon = datetime.now(tz=UTC) + timedelta(hours=hours)
    result = await session.execute(
        select(AgronomyScore)
        .where(
            AgronomyScore.vineyard_id == vineyard_id,
            AgronomyScore.wedge == wedge,
            AgronomyScore.ts >= cutoff,
            AgronomyScore.ts <= horizon,
        )
        .order_by(AgronomyScore.ts)
    )
    return [ScoreResponse.model_validate(s) for s in result.scalars().all()]


@router.get("/forecast")
async def get_forecast(
    vineyard_id: int,
    session: SessionDep,
    hours: int = Query(72, ge=1, le=240),
    model: str = Query("open_meteo"),
) -> list[dict[str, object]]:
    horizon = datetime.now(tz=UTC) + timedelta(hours=hours)
    result = await session.execute(
        select(WeatherForecast)
        .where(
            WeatherForecast.vineyard_id == vineyard_id,
            WeatherForecast.model == model,
            WeatherForecast.valid_ts <= horizon,
        )
        .order_by(WeatherForecast.valid_ts.desc())
        .limit(hours)
    )
    rows = result.scalars().all()
    return [
        {
            "valid_ts": r.valid_ts,
            "init_ts": r.init_ts,
            "t2m": r.t2m,
            "dewpoint": r.dewpoint,
            "rh": r.rh,
            "wind_ms": r.wind_ms,
            "wind_dir": r.wind_dir,
            "precip_mm": r.precip_mm,
            "cloud_frac": r.cloud_frac,
            "sw_rad": r.sw_rad,
        }
        for r in reversed(rows)
    ]
