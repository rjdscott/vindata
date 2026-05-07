"""Raw NASA FIRMS hotspots → MinIO + ``fire_hotspots``.

FIRMS returns a CSV per query; we archive the raw bytes and append rows to
``fire_hotspots`` with a unique-by-coincidence dedupe (drop hotspots whose
(ts, lat, lon) already exists from a previous cycle within ±0.01°).
"""

import json
from datetime import UTC, datetime
from typing import Any

import structlog
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from sqlalchemy import text

from vindata_ingest.resources import FirmsResource, MinioResource, PostgresResource
from vindata_ingest.settings import get_settings

log = structlog.get_logger(__name__)


@asset(
    name="raw_firms",
    group_name="ingest",
    description=(
        "Recent NASA FIRMS active-fire detections in the Orange-region "
        "bounding box. Empty when no FIRMS_MAP_KEY is configured."
    ),
    compute_kind="python",
)
def raw_firms(
    context: AssetExecutionContext,
    minio: MinioResource,
    firms: FirmsResource,
    postgres: PostgresResource,
) -> MaterializeResult:
    settings = get_settings()
    cycle = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    dt = cycle.strftime("%Y-%m-%d")
    hh = cycle.strftime("%H")

    hotspots = firms.recent_hotspots()
    raw_key = f"firms/dt={dt}/cycle={hh}/hotspots.json"
    # Persist normalised JSON (CSV is the source of truth from NASA, but
    # the curated form is more useful for replay / analysis).
    minio.put_bytes(
        settings.raw_bucket,
        raw_key,
        json.dumps(hotspots, default=str, separators=(",", ":")).encode(),
        content_type="application/json",
    )

    if not hotspots:
        context.log.info("FIRMS returned 0 hotspots (or offline)")
        return MaterializeResult(
            metadata={
                "rows": MetadataValue.int(0),
                "raw_key": MetadataValue.text(raw_key),
                "note": MetadataValue.text("no hotspots / offline"),
            }
        )

    inserts: list[dict[str, Any]] = []
    for h in hotspots:
        inserts.append(
            {
                "ts": h["ts"],
                "lon": h["lon"],
                "lat": h["lat"],
                "brightness_k": h.get("brightness_k"),
                "frp_mw": h.get("frp_mw"),
                "satellite": h.get("satellite", "MODIS_NRT"),
                "confidence": h.get("confidence"),
            }
        )

    insert_sql = text("""
        INSERT INTO fire_hotspots
            (ts, geom, brightness_k, frp_mw, satellite, confidence, source)
        SELECT
            :ts,
            ST_GeogFromText('SRID=4326;POINT(' || :lon || ' ' || :lat || ')'),
            :brightness_k, :frp_mw, :satellite, :confidence, 'firms_modis'
        WHERE NOT EXISTS (
            SELECT 1 FROM fire_hotspots fh
            WHERE fh.ts = :ts
              AND ST_DWithin(
                  fh.geom,
                  ST_GeogFromText('SRID=4326;POINT(' || :lon || ' ' || :lat || ')'),
                  500
              )
        )
    """)
    n_inserted = 0
    with postgres.session() as session:
        for params in inserts:
            r = session.execute(insert_sql, params)
            n_inserted += r.rowcount

    return MaterializeResult(
        metadata={
            "rows": MetadataValue.int(n_inserted),
            "raw_key": MetadataValue.text(raw_key),
            "cycle_utc": MetadataValue.text(cycle.isoformat()),
        }
    )
