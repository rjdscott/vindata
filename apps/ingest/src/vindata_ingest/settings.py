"""Ingest-side settings, mirrored against the env vars docker-compose sets."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VINDATA_INGEST_",
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    # Postgres (sync driver — Dagster doesn't run async-engine SQLAlchemy here).
    database_url: str = "postgresql+psycopg://vindata:vindata@postgres:5432/vindata"

    # MinIO / S3-compatible.
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "vindata"
    s3_secret_key: str = "vindatadev"
    raw_bucket: str = "vindata-raw"
    curated_bucket: str = "vindata-curated"

    # Sources.
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1"
    airquality_base_url: str = "https://data.airquality.nsw.gov.au"
    airquality_offline: bool = False
    firms_base_url: str = "https://firms.modaps.eosdis.nasa.gov"
    firms_map_key: str = ""  # Empty → resource is offline, no calls made.
    firms_source: str = "MODIS_NRT"


@lru_cache(maxsize=1)
def get_settings() -> IngestSettings:
    return IngestSettings()
