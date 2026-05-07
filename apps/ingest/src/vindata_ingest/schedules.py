"""Hourly schedule for the full asset graph."""

from __future__ import annotations

from dagster import AssetSelection, ScheduleDefinition, define_asset_job

hourly_job = define_asset_job(
    name="hourly_ingest_and_score",
    selection=AssetSelection.all(),
)

hourly_schedule = ScheduleDefinition(
    name="hourly_ingest",
    cron_schedule="5 * * * *",  # 5 minutes past each hour, gives upstream a moment
    job=hourly_job,
)
