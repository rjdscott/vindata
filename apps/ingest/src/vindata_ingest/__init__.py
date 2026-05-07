"""VinData Dagster code-location.

Asset graph (Stage 00):

    raw_open_meteo_forecast  ──▶  curated_forecast  ──▶  frost_score

Resources: ``MinioResource``, ``PostgresResource``, ``OpenMeteoResource``.

Schedule: hourly. Sensor: backfill the latest 48 h on launch / on-miss.
"""
