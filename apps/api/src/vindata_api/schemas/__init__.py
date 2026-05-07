"""Pydantic v2 response schemas. One file per resource for clarity."""

from vindata_api.schemas.scores import ScoreResponse
from vindata_api.schemas.vineyards import (
    BlockResponse,
    VineyardDetailResponse,
    VineyardSummaryResponse,
)

__all__ = [
    "BlockResponse",
    "ScoreResponse",
    "VineyardDetailResponse",
    "VineyardSummaryResponse",
]
