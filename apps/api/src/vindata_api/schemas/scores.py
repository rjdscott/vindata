"""Score / forecast response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

FrostLevelLiteral = Literal["low", "elevated", "high", "extreme"]
WedgeLiteral = Literal["frost", "dm", "pm", "botrytis", "smoke", "pheno"]


class ScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    lead_h: int
    score: float = Field(..., ge=0, le=1)
    level: FrostLevelLiteral
    wedge: WedgeLiteral
    model_version: str
    inputs: dict[str, Any]
