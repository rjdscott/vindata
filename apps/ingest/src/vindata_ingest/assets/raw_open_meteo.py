"""Raw Open-Meteo forecast → MinIO.

One blob per (vineyard, cycle). The cycle key is computed from "now" rounded
to the hour; we store the raw JSON unmodified so the curation step is the
only place that knows about the response shape.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from dagster import (
    AssetExecutionContext,
    AssetIn,
    MaterializeResult,
    MetadataValue,
    asset,
)

from vindata_ingest.resources import MinioResource, OpenMeteoResource
from vindata_ingest.settings import get_settings

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _PilotVineyard:
    slug: str
    name: str
    lat: float
    lon: float


# Mirror of the API seed list. Kept close to the asset so the ingest job is
# self-contained; Stage 01 reads this from the DB.
PILOT_VINEYARD_LOCATIONS: tuple[_PilotVineyard, ...] = (
    _PilotVineyard("cargo-road", "Cargo Road Wines", -33.317, 148.957),
    _PilotVineyard("placeholder-2", "Vineyard 2 (TBC)", -33.330, 148.985),
    _PilotVineyard("placeholder-3", "Vineyard 3 (TBC)", -33.300, 148.940),
    _PilotVineyard("placeholder-4", "Vineyard 4 (TBC)", -33.350, 148.970),
    _PilotVineyard("placeholder-5", "Vineyard 5 (TBC)", -33.320, 149.020),
    _PilotVineyard("placeholder-6", "Vineyard 6 (TBC)", -33.290, 148.990),
)


@asset(
    name="raw_open_meteo_forecast",
    group_name="ingest",
    description=(
        "Hourly Open-Meteo forecast for each pilot vineyard. "
        "One JSON blob per vineyard per cycle, written to MinIO."
    ),
    compute_kind="python",
)
def raw_open_meteo_forecast(
    context: AssetExecutionContext,
    minio: MinioResource,
    open_meteo: OpenMeteoResource,
) -> MaterializeResult:
    settings = get_settings()
    cycle = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    dt = cycle.strftime("%Y-%m-%d")
    hh = cycle.strftime("%H")

    written: list[str] = []
    for v in PILOT_VINEYARD_LOCATIONS:
        payload = open_meteo.hourly_forecast(lat=v.lat, lon=v.lon)
        key = f"open_meteo/dt={dt}/cycle={hh}/{v.slug}.json"
        minio.put_bytes(
            settings.raw_bucket,
            key,
            json.dumps(payload, separators=(",", ":")).encode(),
            content_type="application/json",
        )
        context.log.info(f"wrote {settings.raw_bucket}/{key}")
        written.append(key)

    return MaterializeResult(
        metadata={
            "cycle_utc": MetadataValue.text(cycle.isoformat()),
            "objects": MetadataValue.int(len(written)),
            "bucket": MetadataValue.text(settings.raw_bucket),
            "sample_key": MetadataValue.text(written[0] if written else ""),
        }
    )


# Re-exported for the curated asset's typed `ins`.
RAW_FORECAST_IN = AssetIn(key="raw_open_meteo_forecast")
