"""Pure-function tests for the curate-step normaliser.

We don't need MinIO or Postgres for this — it's just shape/typing.
"""

from __future__ import annotations

import polars as pl

from vindata_ingest.assets.curated_forecast import _normalise_one


def test_normalise_one_returns_expected_columns() -> None:
    payload = {
        "hourly": {
            "time": ["2026-05-07T00:00", "2026-05-07T01:00"],
            "temperature_2m": [10.0, 9.5],
            "dew_point_2m": [4.0, 3.5],
            "relative_humidity_2m": [80, 82],
            "wind_speed_10m": [1.2, 1.0],
            "wind_direction_10m": [180, 190],
            "precipitation": [0.0, 0.0],
            "cloud_cover": [10, 20],
            "shortwave_radiation": [0, 0],
        }
    }
    df = _normalise_one(payload, "cargo-road")
    assert df.shape == (2, 10)
    assert set(df.columns) == {
        "vineyard_slug", "valid_ts", "t2m", "dewpoint", "rh",
        "wind_ms", "wind_dir", "precip_mm", "cloud_frac", "sw_rad",
    }
    assert df["vineyard_slug"].to_list() == ["cargo-road", "cargo-road"]


def test_normalise_one_empty_when_no_hourly() -> None:
    df = _normalise_one({}, "x")
    assert df.is_empty()


def test_normalise_one_handles_missing_variables() -> None:
    payload = {
        "hourly": {
            "time": ["2026-05-07T00:00"],
            "temperature_2m": [10.0],
            # All other fields missing.
        }
    }
    df = _normalise_one(payload, "x")
    assert df.shape == (1, 10)
    # Missing columns must be filled with nulls, not crash.
    assert df["dewpoint"].null_count() == 1
    assert df["wind_ms"].null_count() == 1
    assert isinstance(df, pl.DataFrame)
