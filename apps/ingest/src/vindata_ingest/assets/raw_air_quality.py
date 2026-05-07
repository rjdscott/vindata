"""Raw NSW DPE PM2.5 → MinIO + ``pm25_observations``.

Pulls the last 24 hours of PM2.5 from the configured stations, attributes
each observation to the *nearest* pilot vineyard (Haversine), and upserts
into Postgres. The raw JSON is also archived to MinIO so future curation
can re-derive against alternative attribution rules.
"""

import json
from datetime import UTC, datetime
from math import asin, cos, radians, sin, sqrt
from typing import Any

import structlog
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from sqlalchemy import text

from vindata_ingest.assets.raw_open_meteo import PILOT_VINEYARD_LOCATIONS
from vindata_ingest.resources import (
    AirQualityResource,
    MinioResource,
    PostgresResource,
)
from vindata_ingest.settings import get_settings

log = structlog.get_logger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km. Earth radius 6371 km."""
    rlat1, rlat2 = radians(lat1), radians(lat2)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(a))


@asset(
    name="raw_air_quality",
    group_name="ingest",
    description=(
        "Recent PM2.5 from NSW DPE Air Quality. Stored raw to MinIO and "
        "attributed to the nearest pilot vineyard in pm25_observations."
    ),
    compute_kind="python",
)
def raw_air_quality(
    context: AssetExecutionContext,
    minio: MinioResource,
    airquality: AirQualityResource,
    postgres: PostgresResource,
) -> MaterializeResult:
    settings = get_settings()
    cycle = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    dt = cycle.strftime("%Y-%m-%d")
    hh = cycle.strftime("%H")

    rows = airquality.recent_pm25(hours=24)
    raw_key = f"airquality/dt={dt}/cycle={hh}/pm25.json"
    minio.put_bytes(
        settings.raw_bucket,
        raw_key,
        json.dumps(rows, default=str, separators=(",", ":")).encode(),
        content_type="application/json",
    )

    if not rows:
        # Live API may be unreachable in the dev sandbox; this is a
        # warning rather than a hard fail so the rest of the graph still
        # renders. The asset check converts a multi-cycle gap to ERROR.
        context.log.warning("airquality returned 0 rows")
        return MaterializeResult(
            metadata={
                "rows": MetadataValue.int(0),
                "raw_key": MetadataValue.text(raw_key),
                "note": MetadataValue.text("offline or empty"),
            }
        )

    # Resolve vineyard_id by slug, attributing each obs to the nearest.
    with postgres.session() as session:
        v_rows = session.execute(
            text("SELECT id, slug, ST_X(centroid::geometry) AS lon, "
                 "ST_Y(centroid::geometry) AS lat FROM vineyards")
        ).all()
    vineyards = [(vid, slug, lon, lat) for (vid, slug, lon, lat) in v_rows]

    upserts: list[dict[str, Any]] = []
    for r in rows:
        # Nearest vineyard among the pilot set.
        nearest_id, _slug, distance_km = min(
            (
                (vid, slug, _haversine_km(r["lat"], r["lon"], lat, lon))
                for (vid, slug, lon, lat) in vineyards
            ),
            key=lambda t: t[2],
        )
        upserts.append(
            {
                "vineyard_id": nearest_id,
                "ts": r["ts"],
                "pm25_ug_m3": r["pm25_ug_m3"],
                "station": r["name"],
                "distance_km": distance_km,
            }
        )

    upsert_sql = text("""
        INSERT INTO pm25_observations
            (vineyard_id, ts, pm25_ug_m3, station, distance_km)
        VALUES
            (:vineyard_id, :ts, :pm25_ug_m3, :station, :distance_km)
        ON CONFLICT (vineyard_id, ts)
        DO UPDATE SET
            pm25_ug_m3 = EXCLUDED.pm25_ug_m3,
            station = EXCLUDED.station,
            distance_km = EXCLUDED.distance_km
    """)
    with postgres.session() as session:
        session.execute(upsert_sql, upserts)

    return MaterializeResult(
        metadata={
            "rows": MetadataValue.int(len(upserts)),
            "raw_key": MetadataValue.text(raw_key),
            "vineyards_attributed": MetadataValue.int(
                len({u["vineyard_id"] for u in upserts})
            ),
            "cycle_utc": MetadataValue.text(cycle.isoformat()),
        }
    )


# Re-export pilot location list for downstream callers that need it.
__all__ = ["PILOT_VINEYARD_LOCATIONS", "raw_air_quality"]
