"""Block-scoped endpoints — currently just phenology state."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from vindata_api.db import SessionDep
from vindata_api.models import Block, PhenologyState
from vindata_api.schemas.scores import PhenologyStateResponse

router = APIRouter(prefix="/v1/blocks/{block_id}", tags=["blocks"])


@router.get("/phenology", response_model=list[PhenologyStateResponse])
async def get_block_phenology(
    block_id: int,
    session: SessionDep,
    days: int = Query(120, ge=1, le=400),
) -> list[PhenologyStateResponse]:
    block = (
        await session.execute(select(Block).where(Block.id == block_id))
    ).scalar_one_or_none()
    if block is None:
        raise HTTPException(status_code=404, detail="block not found")

    cutoff = (datetime.now(tz=UTC) - timedelta(days=days)).date()
    rows = (
        await session.execute(
            select(PhenologyState)
            .where(
                PhenologyState.block_id == block_id,
                PhenologyState.date >= cutoff,
            )
            .order_by(PhenologyState.date)
        )
    ).scalars().all()
    return [PhenologyStateResponse.model_validate(r) for r in rows]
