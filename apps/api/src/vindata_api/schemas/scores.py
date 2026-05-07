"""Score / forecast / phenology response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

LevelLiteral = Literal["low", "elevated", "high", "extreme"]
WedgeLiteral = Literal["frost", "dm", "pm", "botrytis", "smoke", "pheno"]
# Backward-compat alias — routers / tests may still reference the old name.
FrostLevelLiteral = LevelLiteral


class ScoreResponse(BaseModel):
    """One row from ``agronomy_scores``.

    The ``score`` field is normalised to [0, 1] across all wedges so the
    UI can render a uniform sparkline / chip without per-wedge logic. The
    raw native units (DSV, Gubler-Thomas index, smoke dose µg·h/m³, etc.)
    are surfaced in ``inputs`` for analytical drill-down.
    """

    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    lead_h: int
    score: float = Field(..., ge=0, le=1)
    level: LevelLiteral
    wedge: WedgeLiteral
    model_version: str
    inputs: dict[str, Any]


class PhenologyStateResponse(BaseModel):
    """One row from ``phenology_state`` for a block."""

    model_config = ConfigDict(from_attributes=True)

    block_id: int
    date: date
    doy: int
    chill_units: float
    forcing_dd: float
    gdd_from_budbreak: float
    bbch: int
    model_version: str
