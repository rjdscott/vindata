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
    assert "raw_air_quality" in keys
    assert "raw_firms" in keys
    assert "curated_forecast" in keys
    assert "phenology_state" in keys
    assert "frost_score" in keys
    assert "disease_score" in keys
    assert "smoke_score" in keys


def test_score_dependencies_correct() -> None:
    """Phenology must run before disease + smoke so they can read BBCH."""
    graph = defs.resolve_asset_graph()

    def deps_of(name: str) -> set[str]:
        for key in graph.get_all_asset_keys():
            if key.to_user_string() == name:
                return {p.to_user_string() for p in graph.get(key).parent_keys}
        return set()

    assert "phenology_state" in deps_of("disease_score")
    assert "phenology_state" in deps_of("smoke_score")
    assert "raw_air_quality" in deps_of("smoke_score")
