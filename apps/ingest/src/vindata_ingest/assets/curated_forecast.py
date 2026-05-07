"""Curate raw Open-Meteo into normalised forecast rows.

Reads the most recent raw cycle from MinIO, normalises to a long-form table
``(vineyard_id, model, init_ts, valid_ts, t2m, dewpoint, rh, ...)``, writes
Parquet to ``s3://vindata-curated/forecast/...``, and upserts into Postgres
``weather_forecasts``.
"""

import io
import json
from datetime import UTC, datetime
from typing import cast

import polars as pl
import structlog
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from sqlalchemy import text

from vindata_ingest.assets.raw_open_meteo import (
    PILOT_VINEYARD_LOCATIONS,
    raw_open_meteo_forecast,
)
from vindata_ingest.resources import MinioResource, PostgresResource
from vindata_ingest.settings import get_settings

log = structlog.get_logger(__name__)

_FORECAST_MODEL_NAME = "open_meteo"


def _normalise_one(payload: dict[str, object], slug: str) -> pl.DataFrame:
    """Open-Meteo response → long-form DataFrame with our column names."""
    hourly = cast("dict[str, list[object]]", payload.get("hourly", {}))
    times = hourly.get("time", [])
    n = len(times)
    if n == 0:
        return pl.DataFrame()

    return pl.DataFrame(
        {
            "vineyard_slug": [slug] * n,
            "valid_ts": times,
            "t2m": hourly.get("temperature_2m", [None] * n),
            "dewpoint": hourly.get("dew_point_2m", [None] * n),
            "rh": hourly.get("relative_humidity_2m", [None] * n),
            "wind_ms": hourly.get("wind_speed_10m", [None] * n),
            "wind_dir": hourly.get("wind_direction_10m", [None] * n),
            "precip_mm": hourly.get("precipitation", [None] * n),
            "cloud_frac": hourly.get("cloud_cover", [None] * n),
            "sw_rad": hourly.get("shortwave_radiation", [None] * n),
        }
    )


@asset(
    name="curated_forecast",
    group_name="curate",
    deps=[raw_open_meteo_forecast],
    description="Normalises raw Open-Meteo forecasts to Parquet + Postgres.",
    compute_kind="python",
)
def curated_forecast(
    context: AssetExecutionContext,
    minio: MinioResource,
    postgres: PostgresResource,
) -> MaterializeResult:
    settings = get_settings()
    cycle = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    dt = cycle.strftime("%Y-%m-%d")
    hh = cycle.strftime("%H")

    frames: list[pl.DataFrame] = []
    for v in PILOT_VINEYARD_LOCATIONS:
        key = f"open_meteo/dt={dt}/cycle={hh}/{v.slug}.json"
        try:
            blob = minio.get_bytes(settings.raw_bucket, key)
        except Exception as e:
            context.log.warning(f"raw not yet present for {v.slug}: {e}")
            continue
        payload = json.loads(blob)
        df = _normalise_one(payload, v.slug)
        if not df.is_empty():
            df = df.with_columns(pl.col("valid_ts").str.to_datetime(time_zone="UTC"))
            frames.append(df)

    if not frames:
        return MaterializeResult(
            metadata={"rows": MetadataValue.int(0), "note": MetadataValue.text("no raw")}
        )

    df = pl.concat(frames, how="vertical")

    # Resolve vineyard_id by slug; do it in one round-trip.
    with postgres.session() as session:
        rows = session.execute(text("SELECT id, slug FROM vineyards")).all()
    slug_to_id = {slug: vid for (vid, slug) in rows}
    df = df.with_columns(
        pl.col("vineyard_slug").replace_strict(slug_to_id, default=None).alias("vineyard_id")
    ).drop_nulls("vineyard_id")

    df = df.with_columns(
        pl.lit(_FORECAST_MODEL_NAME).alias("model"),
        pl.lit(cycle).alias("init_ts"),
    )

    # ----- write curated Parquet -----
    parquet_key = f"forecast/dt={dt}/cycle={hh}/forecast.parquet"
    buf = io.BytesIO()
    df.write_parquet(buf)
    minio.put_bytes(
        settings.curated_bucket, parquet_key, buf.getvalue(),
        content_type="application/octet-stream",
    )

    # ----- upsert into Postgres -----
    cols = [
        "vineyard_id", "model", "init_ts", "valid_ts",
        "t2m", "dewpoint", "rh", "wind_ms", "wind_dir",
        "precip_mm", "cloud_frac", "sw_rad",
    ]
    records = df.select(cols).to_dicts()

    upsert_sql = text("""
        INSERT INTO weather_forecasts
            (vineyard_id, model, init_ts, valid_ts, t2m, dewpoint, rh,
             wind_ms, wind_dir, precip_mm, cloud_frac, sw_rad)
        VALUES
            (:vineyard_id, :model, :init_ts, :valid_ts, :t2m, :dewpoint, :rh,
             :wind_ms, :wind_dir, :precip_mm, :cloud_frac, :sw_rad)
        ON CONFLICT (vineyard_id, model, init_ts, valid_ts)
        DO UPDATE SET
            t2m = EXCLUDED.t2m,
            dewpoint = EXCLUDED.dewpoint,
            rh = EXCLUDED.rh,
            wind_ms = EXCLUDED.wind_ms,
            wind_dir = EXCLUDED.wind_dir,
            precip_mm = EXCLUDED.precip_mm,
            cloud_frac = EXCLUDED.cloud_frac,
            sw_rad = EXCLUDED.sw_rad
    """)
    with postgres.session() as session:
        session.execute(upsert_sql, records)

    return MaterializeResult(
        metadata={
            "rows": MetadataValue.int(len(records)),
            "vineyards": MetadataValue.int(len(slug_to_id)),
            "parquet_key": MetadataValue.text(parquet_key),
            "cycle_utc": MetadataValue.text(cycle.isoformat()),
        }
    )
