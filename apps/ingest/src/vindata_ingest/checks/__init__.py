"""Dagster asset checks.

Asset checks live in their own module so they're easy to discover and
extend wedge-by-wedge in Stage 01. They are first-class in Dagster's UI
and run as part of every materialisation; failures surface red rather than
silently producing bad scores.

Reference: https://docs.dagster.io/concepts/assets/asset-checks
"""

from vindata_ingest.checks.curated_forecast_checks import (
    forecast_temperatures_in_range,
    forecast_valid_ts_monotone,
    forecast_variables_not_null,
)

__all__ = [
    "forecast_temperatures_in_range",
    "forecast_valid_ts_monotone",
    "forecast_variables_not_null",
]
