"""Top-level Dagster ``Definitions`` object.

``workspace.yaml`` references this module; ``defs`` is the conventional name.
"""

from __future__ import annotations

from dagster import Definitions

from vindata_ingest.assets import (
    curated_forecast,
    frost_score,
    raw_open_meteo_forecast,
)
from vindata_ingest.checks import (
    forecast_temperatures_in_range,
    forecast_valid_ts_monotone,
    forecast_variables_not_null,
)
from vindata_ingest.resources import (
    MinioResource,
    OpenMeteoResource,
    PostgresResource,
)
from vindata_ingest.schedules import hourly_schedule
from vindata_ingest.settings import get_settings

_settings = get_settings()

defs = Definitions(
    assets=[raw_open_meteo_forecast, curated_forecast, frost_score],
    asset_checks=[
        forecast_variables_not_null,
        forecast_temperatures_in_range,
        forecast_valid_ts_monotone,
    ],
    resources={
        "minio": MinioResource(
            endpoint_url=_settings.s3_endpoint_url,
            access_key=_settings.s3_access_key,
            secret_key=_settings.s3_secret_key,
        ),
        "open_meteo": OpenMeteoResource(base_url=_settings.open_meteo_base_url),
        "postgres": PostgresResource(database_url=_settings.database_url),
    },
    schedules=[hourly_schedule],
)
