"""Dagster resources: MinIO, Postgres, Open-Meteo, NSW DPE Air Quality,
NASA FIRMS. Each one is a thin adapter over a vendor SDK that we can
swap during tests (offline mode for the network-bound ones)."""

from vindata_ingest.resources.airquality import (
    DEFAULT_STATIONS,
    AirQualityResource,
    AirQualityStation,
)
from vindata_ingest.resources.firms import (
    ORANGE_REGION_BBOX,
    BoundingBox,
    FirmsResource,
)
from vindata_ingest.resources.minio_io import MinioResource
from vindata_ingest.resources.open_meteo import OpenMeteoResource
from vindata_ingest.resources.postgres import PostgresResource

__all__ = [
    "DEFAULT_STATIONS",
    "ORANGE_REGION_BBOX",
    "AirQualityResource",
    "AirQualityStation",
    "BoundingBox",
    "FirmsResource",
    "MinioResource",
    "OpenMeteoResource",
    "PostgresResource",
]
