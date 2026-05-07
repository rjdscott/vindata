"""Smoke-taint score asset — per-block daily dose.

Reads the last 24 h of attributed PM2.5 from ``pm25_observations``,
classifies each hour's boundary-layer stability from cloud_frac and wind,
applies the block's current BBCH weighting, and writes a ``smoke`` row
to ``agronomy_scores``.
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from sqlalchemy import text

from agronomy import SMOKE_MODEL_VERSION
from agronomy.phenology import BBCH
from agronomy.smoke import LEVEL_HIGH_MAX, HourlyExposure, smoke_dose_index
from vindata_ingest.assets.phenology_state import phenology_state
from vindata_ingest.assets.raw_air_quality import raw_air_quality
from vindata_ingest.resources import PostgresResource

log = structlog.get_logger(__name__)


def _stability(cloud_frac: float | None, wind_ms: float | None) -> str:
    """Heuristic boundary-layer stability classification.

    For PoC we use a coarse three-class cloud+wind heuristic; Stage 01
    refits using ACCESS-G's actual stability diagnostic (Pasquill class).
    """
    cf = 1.0 if cloud_frac is None else float(cloud_frac) / 100.0
    w = 0.0 if wind_ms is None else float(wind_ms)
    if cf < 0.3 and w < 2.0:
        return "stable"
    if cf > 0.5:
        return "unstable"
    return "neutral"


@asset(
    name="smoke_score",
    group_name="score",
    deps=[phenology_state, raw_air_quality],
    description="Per-block daily smoke-taint dose from agronomy.smoke.",
    compute_kind="python",
)
def smoke_score(
    context: AssetExecutionContext,
    postgres: PostgresResource,
) -> MaterializeResult:
    cycle_day = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    window_start = cycle_day - timedelta(hours=24)

    blocks_sql = text("""
        SELECT b.id AS block_id, b.vineyard_id,
               COALESCE(p.bbch, 0) AS bbch
        FROM blocks b
        LEFT JOIN LATERAL (
            SELECT bbch FROM phenology_state
            WHERE block_id = b.id AND date <= CURRENT_DATE
            ORDER BY date DESC LIMIT 1
        ) p ON TRUE
    """)
    pm_sql = text("""
        SELECT pm.ts, pm.pm25_ug_m3
        FROM pm25_observations pm
        WHERE pm.vineyard_id = :vid
          AND pm.ts >= :start
          AND pm.ts < :cycle
        ORDER BY pm.ts
    """)
    weather_sql = text("""
        SELECT valid_ts, cloud_frac, wind_ms FROM weather_forecasts
        WHERE vineyard_id = :vid
          AND model = 'open_meteo'
          AND valid_ts >= :start
          AND valid_ts < :cycle
        ORDER BY valid_ts
    """)
    upsert_sql = text("""
        INSERT INTO agronomy_scores
            (vineyard_id, block_id, wedge, ts, lead_h, score, level,
             inputs, model_version)
        VALUES
            (:vineyard_id, :block_id, 'smoke', :ts, :lead_h, :score, :level,
             CAST(:inputs AS JSON), :model_version)
        ON CONFLICT ON CONSTRAINT pk_agronomy_scores
        DO UPDATE SET
            score = EXCLUDED.score,
            level = EXCLUDED.level,
            inputs = EXCLUDED.inputs,
            model_version = EXCLUDED.model_version
    """)

    rows_written = 0
    with postgres.session() as session:
        blocks = session.execute(blocks_sql).all()
        upserts: list[dict[str, Any]] = []
        for block_id, vineyard_id, bbch_int in blocks:
            pm_rows = session.execute(
                pm_sql, {"vid": vineyard_id, "start": window_start, "cycle": cycle_day}
            ).all()
            wx_rows = session.execute(
                weather_sql,
                {"vid": vineyard_id, "start": window_start, "cycle": cycle_day},
            ).all()
            wx_by_hour = {
                ts.replace(minute=0, second=0, microsecond=0): (cf, w)
                for ts, cf, w in wx_rows
            }

            hours: list[HourlyExposure] = []
            for ts, pm in pm_rows:
                cf, w = wx_by_hour.get(
                    ts.replace(minute=0, second=0, microsecond=0), (None, None)
                )
                try:
                    hours.append(
                        HourlyExposure(
                            pm25_ug_m3=max(0.0, float(pm)),
                            stability=_stability(cf, w),
                        )
                    )
                except ValueError:
                    continue

            bbch = BBCH(int(bbch_int)) if int(bbch_int) in {b.value for b in BBCH} else BBCH.DORMANT
            dose = smoke_dose_index(hours, bbch=bbch)

            # Normalise to [0,1] using LEVEL_HIGH_MAX so sustained "high"
            # dose maps to score 1.0 — extreme is unbounded but rare.
            score = min(1.0, dose.dose / LEVEL_HIGH_MAX)

            ts = cycle_day.replace(hour=0, minute=0, second=0, microsecond=0)
            upserts.append(
                {
                    "vineyard_id": vineyard_id,
                    "block_id": block_id,
                    "ts": ts,
                    "lead_h": 0,
                    "score": score,
                    "level": dose.level,
                    "inputs": json.dumps(
                        {
                            "dose": dose.dose,
                            "pm25_mean": dose.pm25_mean,
                            "pm25_max": dose.pm25_max,
                            "hours_smoky": dose.hours_smoky,
                            "bbch": int(bbch),
                            "samples": len(hours),
                        }
                    ),
                    "model_version": SMOKE_MODEL_VERSION,
                }
            )
            rows_written += 1

        if upserts:
            session.execute(upsert_sql, upserts)

    return MaterializeResult(
        metadata={
            "rows": MetadataValue.int(rows_written),
            "model_version": MetadataValue.text(SMOKE_MODEL_VERSION),
            "cycle_utc": MetadataValue.text(cycle_day.isoformat()),
        }
    )
