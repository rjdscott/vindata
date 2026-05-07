"""Top-level Dagster ``Definitions`` object.

``workspace.yaml`` references this module; ``defs`` is the conventional name.
"""

from __future__ import annotations

from dagster import Definitions

from vindata_ingest.assets import (
    curated_forecast,
    disease_score,
    frost_score,
    phenology_state,
    raw_air_quality,
    raw_firms,
    raw_open_meteo_forecast,
    smoke_score,
)
from vindata_ingest.checks import (
    disease_dm_rows_written,
    disease_score_in_unit_interval,
    forecast_temperatures_in_range,
    forecast_valid_ts_monotone,
    forecast_variables_not_null,
    phenology_bbch_in_range,
    smoke_score_in_unit_interval,
)
from vindata_ingest.resources import (
    AirQualityResource,
    FirmsResource,
    MinioResource,
    OpenMeteoResource,
    PostgresResource,
)
from vindata_ingest.schedules import hourly_schedule
from vindata_ingest.settings import get_settings

_settings = get_settings()

defs = Definitions(
    assets=[
        # ingest
        raw_open_meteo_forecast,
        raw_air_quality,
        raw_firms,
        # curate
        curated_forecast,
        # score (phenology must run first so disease/smoke can read BBCH)
        phenology_state,
        frost_score,
        disease_score,
        smoke_score,
    ],
    asset_checks=[
        forecast_variables_not_null,
        forecast_temperatures_in_range,
        forecast_valid_ts_monotone,
        phenology_bbch_in_range,
        disease_dm_rows_written,
        disease_score_in_unit_interval,
        smoke_score_in_unit_interval,
    ],
    resources={
        "minio": MinioResource(
            endpoint_url=_settings.s3_endpoint_url,
            access_key=_settings.s3_access_key,
            secret_key=_settings.s3_secret_key,
        ),
        "open_meteo": OpenMeteoResource(base_url=_settings.open_meteo_base_url),
        "airquality": AirQualityResource(
            base_url=_settings.airquality_base_url,
            offline=_settings.airquality_offline,
        ),
        "firms": FirmsResource(
            base_url=_settings.firms_base_url,
            map_key=_settings.firms_map_key,
            source=_settings.firms_source,
        ),
        "postgres": PostgresResource(database_url=_settings.database_url),
    },
    schedules=[hourly_schedule],
)
