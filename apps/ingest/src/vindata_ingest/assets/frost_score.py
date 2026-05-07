"""Frost score asset.

Reads the latest forecast rows for each vineyard from Postgres, runs the
agronomy frost model per ``valid_ts``, and upserts results into
``agronomy_scores`` with ``wedge='frost'``.

Hours-since-sunset is approximated using a fixed nominal sunset of 18:00
local time (Australia/Sydney, UTC+10/+11). At Stage 00 this is good enough;
Stage 01 will compute astronomical sunset per latitude.
"""

import json
from datetime import UTC, datetime, timedelta

import structlog
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from sqlalchemy import text

from agronomy import (
    ForecastSample,
    FrostParams,
    predict_tmin,
    score_frost,
)
from agronomy.version import FROST_MODEL_VERSION
from vindata_ingest.assets.curated_forecast import curated_forecast
from vindata_ingest.resources import PostgresResource

log = structlog.get_logger(__name__)

# Australia/Sydney is UTC+10 (AEST) or UTC+11 (AEDT). For Stage 00 we use a
# fixed offset of +10h; Stage 01 uses real timezone-aware sunset times.
_LOCAL_OFFSET_H = 10
_NOMINAL_SUNSET_LOCAL_HOUR = 18


def _hours_since_sunset(valid_ts_utc: datetime) -> float:
    """Wallclock hours from the previous local 18:00 to ``valid_ts_utc``.

    Always non-negative. Daytime samples (e.g. local 14:00) get a value
    representing time since the *previous* sunset, which the radiation model
    multiplies by ``sqrt(t)`` and produces a large cooling — undesirable for
    daytime but harmless at Stage 00 because daytime samples are dominated
    by ``t2m`` not ``Tmin_pred`` in the UI. The downstream UI shows
    ``Tmin_pred`` as a separate line; users see the meaningful overnight
    minima.
    """
    local = valid_ts_utc + timedelta(hours=_LOCAL_OFFSET_H)
    sunset_local = local.replace(
        hour=_NOMINAL_SUNSET_LOCAL_HOUR, minute=0, second=0, microsecond=0
    )
    if local < sunset_local:
        sunset_local -= timedelta(days=1)
    return (local - sunset_local).total_seconds() / 3600.0


@asset(
    name="frost_score",
    group_name="score",
    deps=[curated_forecast],
    description="Per-vineyard hourly frost score from the agronomy library.",
    compute_kind="python",
)
def frost_score(
    context: AssetExecutionContext,
    postgres: PostgresResource,
) -> MaterializeResult:
    cycle = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    horizon = cycle + timedelta(hours=72)
    params = FrostParams()

    select_sql = text("""
        SELECT vineyard_id, init_ts, valid_ts, t2m, dewpoint, wind_ms, cloud_frac
        FROM weather_forecasts
        WHERE model = 'open_meteo'
          AND valid_ts >= :cycle
          AND valid_ts <= :horizon
        ORDER BY vineyard_id, valid_ts
    """)
    upsert_sql = text("""
        INSERT INTO agronomy_scores
            (vineyard_id, block_id, wedge, ts, lead_h, score, level,
             inputs, model_version)
        VALUES
            (:vineyard_id, NULL, 'frost', :ts, :lead_h, :score, :level,
             CAST(:inputs AS JSON), :model_version)
        ON CONFLICT ON CONSTRAINT pk_agronomy_scores
        DO UPDATE SET
            score = EXCLUDED.score,
            level = EXCLUDED.level,
            inputs = EXCLUDED.inputs,
            model_version = EXCLUDED.model_version
    """)

    n_rows = 0
    n_skipped_invalid = 0
    with postgres.session() as session:
        rows = session.execute(
            select_sql, {"cycle": cycle, "horizon": horizon}
        ).all()
        records: list[dict[str, object]] = []
        for r in rows:
            (vineyard_id, init_ts, valid_ts, t2m, dewpoint, wind_ms, cloud_frac) = r
            # Skip if any input is null (Open-Meteo occasionally returns nulls
            # at the very edge of the forecast horizon).
            if None in (t2m, dewpoint, wind_ms, cloud_frac):
                n_skipped_invalid += 1
                continue
            try:
                # Defensive: open-meteo can return dewpoint marginally above
                # t2m at low precision; clip to t2m before constructing the
                # sample so the boundary validator doesn't reject it.
                td = min(float(dewpoint), float(t2m))
                cf = max(0.0, min(1.0, float(cloud_frac) / 100.0))
                sample = ForecastSample(
                    t2m_c=float(t2m),
                    dewpoint_c=td,
                    wind_ms=float(wind_ms),
                    cloud_frac=cf,
                    hours_since_sunset=_hours_since_sunset(valid_ts),
                )
            except ValueError:
                n_skipped_invalid += 1
                continue
            tmin = predict_tmin(sample, params)
            score = score_frost(tmin, sample)
            lead_h = int((valid_ts - init_ts).total_seconds() / 3600.0)
            records.append(
                {
                    "vineyard_id": vineyard_id,
                    "ts": valid_ts,
                    "lead_h": lead_h,
                    "score": score.score,
                    "level": score.level.value,
                    "inputs": json.dumps(score.inputs),
                    "model_version": FROST_MODEL_VERSION,
                }
            )
        if records:
            session.execute(upsert_sql, records)
            n_rows = len(records)

    return MaterializeResult(
        metadata={
            "rows": MetadataValue.int(n_rows),
            "skipped_invalid": MetadataValue.int(n_skipped_invalid),
            "model_version": MetadataValue.text(FROST_MODEL_VERSION),
            "cycle_utc": MetadataValue.text(cycle.isoformat()),
        }
    )
