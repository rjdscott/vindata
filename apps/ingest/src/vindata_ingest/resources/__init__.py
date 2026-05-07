"""Dagster resources: MinIO, Postgres, Open-Meteo. Each one is a thin
adapter over a vendor SDK that we can swap during tests."""

from vindata_ingest.resources.minio_io import MinioResource
from vindata_ingest.resources.open_meteo import OpenMeteoResource
from vindata_ingest.resources.postgres import PostgresResource

__all__ = ["MinioResource", "OpenMeteoResource", "PostgresResource"]
