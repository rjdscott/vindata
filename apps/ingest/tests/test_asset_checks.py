"""Asset-check registration tests.

We don't run the SQL here (that needs Postgres + a populated DB and is
exercised by the live smoke). We confirm the checks are registered
against ``curated_forecast`` and that their names match what we'll see
in the Dagster UI.
"""

from __future__ import annotations

from vindata_ingest.definitions import defs


def test_asset_checks_registered() -> None:
    spec_names = {
        spec.name
        for spec in defs.resolve_asset_graph().asset_check_keys
    }
    assert "forecast_variables_not_null" in spec_names
    assert "forecast_temperatures_in_range" in spec_names
    assert "forecast_valid_ts_monotone" in spec_names


def test_blocking_checks_are_marked_blocking() -> None:
    graph = defs.resolve_asset_graph()
    for key in graph.asset_check_keys:
        node = graph.get_check_spec(key)
        if key.name in {
            "forecast_variables_not_null",
            "forecast_temperatures_in_range",
        }:
            assert node.blocking, f"{key.name} should block downstream materialisation"
