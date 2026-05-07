"""Pydantic schema validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vindata_api.schemas.scores import ScoreResponse
from vindata_api.schemas.vineyards import (
    BlockResponse,
    VineyardSummaryResponse,
)


def test_vineyard_summary_centroid_round_trips() -> None:
    v = VineyardSummaryResponse(
        id=1,
        slug="cargo-road",
        name="Cargo Road",
        region="Orange NSW",
        centroid={"lat": -33.317, "lon": 148.957},
    )
    assert v.centroid.lat == -33.317
    assert v.centroid.lon == 148.957


def test_centroid_rejects_out_of_range_lat() -> None:
    with pytest.raises(ValueError, match="lat"):
        VineyardSummaryResponse(
            id=1, slug="x", name="x", region="r",
            centroid={"lat": 999.0, "lon": 0.0},
        )


def test_block_optional_fields_default_to_none() -> None:
    b = BlockResponse(id=1, name="Block A")
    assert b.cultivar is None
    assert b.elevation_m is None


def test_score_clamped_to_unit_interval() -> None:
    with pytest.raises(ValueError, match="less than or equal"):
        ScoreResponse(
            ts=datetime.now(tz=UTC),
            lead_h=1,
            score=1.5,
            level="extreme",
            wedge="frost",
            model_version="frost@0.1.0",
            inputs={},
        )


def test_score_level_must_be_known() -> None:
    with pytest.raises(ValueError):
        ScoreResponse(
            ts=datetime.now(tz=UTC),
            lead_h=1,
            score=0.5,
            level="totally-unknown",  # type: ignore[arg-type]
            wedge="frost",
            model_version="frost@0.1.0",
            inputs={},
        )
