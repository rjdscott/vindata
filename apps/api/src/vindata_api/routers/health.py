"""Health probe.

``/v1/health`` returns 200 with a JSON body once the API process is up. A
deeper liveness check (DB reachable) is `/v1/health/ready`. We deliberately
keep ``/v1/health`` cheap so it's safe for high-frequency synthetic monitors
and for Docker healthchecks.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from vindata_api.db import SessionDep

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe (DB included)")
async def readiness(session: SessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}
