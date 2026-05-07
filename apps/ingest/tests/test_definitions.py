"""Smoke that the Definitions object loads end-to-end (asset graph valid)."""

from __future__ import annotations

from vindata_ingest.definitions import defs


def test_definitions_load() -> None:
    # Just touching `defs` validates the Dagster Definitions object — Dagster
    # raises at construction if the asset graph has a cycle, missing dep, or
    # resource is not provided.
    assert defs is not None


def test_expected_assets_present() -> None:
    keys = {
        key.to_user_string()
        for key in defs.resolve_asset_graph().get_all_asset_keys()
    }
    assert "raw_open_meteo_forecast" in keys
    assert "curated_forecast" in keys
    assert "frost_score" in keys
