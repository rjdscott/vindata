"""Disease score asset — three wedges (DM / PM / Botrytis) per block per day.

Reads the next 24 h of hourly forecasts per block, builds an
``HourlyWeather`` window via the NEWA CART LWD proxy, and runs all three
disease models. Results land in ``agronomy_scores`` with normalised
``score`` ∈ [0, 1] and the raw model output (DSV, index, probability) in
``inputs`` so the dashboard can drill down.

Powdery and Botrytis are gated on BBCH ≥ 53 (inflorescences emerging);
pre-flowering blocks see only the downy-mildew wedge.
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

from agronomy import (
    BOTRYTIS_MODEL_VERSION,
    DM_MODEL_VERSION,
    PM_MODEL_VERSION,
)
from agronomy.disease import (
    HourlyWeather,
    botrytis_infection_probability,
    dmcast_dsv,
    gubler_thomas_index,
    hourly_lwd,
    mean_temp_during_wet,
)
from vindata_ingest.assets.phenology_state import phenology_state
from vindata_ingest.resources import PostgresResource

log = structlog.get_logger(__name__)

#: BBCH 53 (inflorescences emerging) — PM/Botrytis only score from here.
BBCH_FLOWER_GATE: int = 53

#: Normalisation caps so all three wedges share the [0, 1] score column.
DM_DSV_CAP: int = 4  # Single-day DSV maxes at 4.
PM_INDEX_CAP: int = 100  # Gubler-Thomas index ceiling.


@asset(
    name="disease_score",
    group_name="score",
    deps=[phenology_state],
    description="Per-block daily DM/PM/Botrytis wedges from agronomy.disease.",
    compute_kind="python",
)
def disease_score(  # noqa: PLR0915 — three wedges in one asset is intentional
    context: AssetExecutionContext,
    postgres: PostgresResource,
) -> MaterializeResult:
    cycle_day = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    horizon = cycle_day + timedelta(hours=24)

    # Per-block forecast window keyed off the vineyard's hourly forecast.
    fc_sql = text("""
        SELECT b.id AS block_id, b.vineyard_id,
               f.valid_ts, f.t2m, f.dewpoint, f.rh, f.precip_mm, f.init_ts
        FROM blocks b
        JOIN weather_forecasts f ON f.vineyard_id = b.vineyard_id
        WHERE f.model = 'open_meteo'
          AND f.valid_ts >= :cycle
          AND f.valid_ts < :horizon
        ORDER BY b.id, f.valid_ts
    """)
    bbch_sql = text("""
        SELECT block_id, MAX(bbch) AS bbch
        FROM phenology_state
        WHERE date <= CURRENT_DATE
        GROUP BY block_id
    """)
    upsert_sql = text("""
        INSERT INTO agronomy_scores
            (vineyard_id, block_id, wedge, ts, lead_h, score, level,
             inputs, model_version)
        VALUES
            (:vineyard_id, :block_id, :wedge, :ts, :lead_h, :score, :level,
             CAST(:inputs AS JSON), :model_version)
        ON CONFLICT ON CONSTRAINT pk_agronomy_scores
        DO UPDATE SET
            score = EXCLUDED.score,
            level = EXCLUDED.level,
            inputs = EXCLUDED.inputs,
            model_version = EXCLUDED.model_version
    """)

    rows_written: dict[str, int] = {"dm": 0, "pm": 0, "botrytis": 0}
    blocks_scored = 0

    with postgres.session() as session:
        bbch_by_block = {bid: int(b or 0) for bid, b in session.execute(bbch_sql).all()}

        # Group forecast rows by block.
        rows = session.execute(fc_sql, {"cycle": cycle_day, "horizon": horizon}).all()
        per_block: dict[
            int, list[tuple[int, datetime, datetime, float, float, float, float]]
        ] = {}
        for r in rows:
            block_id, vineyard_id, valid_ts, t2m, dewpoint, rh, precip, init_ts = r
            per_block.setdefault(block_id, []).append(
                (vineyard_id, valid_ts, init_ts, t2m, dewpoint, rh, precip)
            )

        upserts: list[dict[str, Any]] = []
        for block_id, samples in per_block.items():
            if not samples:
                continue
            blocks_scored += 1

            # Build HourlyWeather where inputs are non-null and physically plausible.
            hours: list[HourlyWeather] = []
            vineyard_id = samples[0][0]
            init_ts = samples[0][2]
            for _, _, _, t2m, dewpoint, rh, precip in samples:
                if None in (t2m, dewpoint, rh, precip):
                    continue
                td = min(float(dewpoint), float(t2m))
                try:
                    hours.append(
                        HourlyWeather(
                            t2m_c=float(t2m),
                            dewpoint_c=td,
                            rh_pct=max(0.0, min(100.0, float(rh))),
                            precip_mm=max(0.0, float(precip)),
                        )
                    )
                except ValueError:
                    continue
            if not hours:
                continue

            ts = cycle_day.replace(hour=0, minute=0, second=0, microsecond=0)
            lead_h = int((ts - init_ts).total_seconds() / 3600.0)
            current_bbch = bbch_by_block.get(block_id, 0)

            # ---- DM (DMCast DSV) — always scored. ----
            dm = dmcast_dsv(hours)
            dm_score = min(1.0, dm.dsv / DM_DSV_CAP)
            dm_level = _dsv_to_level(dm.dsv)
            upserts.append(
                _row(
                    vineyard_id, block_id, "dm", ts, lead_h, dm_score, dm_level,
                    {
                        "dsv": dm.dsv,
                        "lwd_hours": dm.lwd_hours,
                        "t_mean_wet_c": dm.t_mean_wet_c,
                        "bbch": current_bbch,
                    },
                    DM_MODEL_VERSION,
                )
            )
            rows_written["dm"] += 1

            # ---- PM (Gubler-Thomas) — gated on BBCH ≥ 53. ----
            if current_bbch >= BBCH_FLOWER_GATE:
                pm = gubler_thomas_index(hours, prior_index=0)
                pm_score = min(1.0, pm.new_index / PM_INDEX_CAP)
                pm_level = _gt_index_to_level(pm.new_index)
                upserts.append(
                    _row(
                        vineyard_id, block_id, "pm", ts, lead_h, pm_score, pm_level,
                        {
                            "index": pm.new_index,
                            "delta": pm.delta,
                            "optimum_blocks": pm.optimum_blocks,
                            "had_lethal": pm.had_lethal,
                            "bbch": current_bbch,
                        },
                        PM_MODEL_VERSION,
                    )
                )
                rows_written["pm"] += 1

            # ---- Botrytis (Broome) — gated on BBCH ≥ 53. ----
            if current_bbch >= BBCH_FLOWER_GATE:
                lwd = hourly_lwd(hours)
                t_wet = mean_temp_during_wet(hours)
                if lwd >= 6 and t_wet is not None:
                    risk = botrytis_infection_probability(t_wet, lwd_hours=float(lwd))
                    bot_level = _prob_to_level(risk.probability)
                    upserts.append(
                        _row(
                            vineyard_id, block_id, "botrytis", ts, lead_h,
                            risk.probability, bot_level,
                            {
                                "probability": risk.probability,
                                "lwd_hours": lwd,
                                "t_mean_wet_c": t_wet,
                                "in_envelope": risk.in_envelope,
                                "bbch": current_bbch,
                            },
                            BOTRYTIS_MODEL_VERSION,
                        )
                    )
                    rows_written["botrytis"] += 1

        if upserts:
            session.execute(upsert_sql, upserts)

    return MaterializeResult(
        metadata={
            "blocks": MetadataValue.int(blocks_scored),
            "dm_rows": MetadataValue.int(rows_written["dm"]),
            "pm_rows": MetadataValue.int(rows_written["pm"]),
            "botrytis_rows": MetadataValue.int(rows_written["botrytis"]),
            "cycle_utc": MetadataValue.text(cycle_day.isoformat()),
        }
    )


def _row(
    vineyard_id: int,
    block_id: int,
    wedge: str,
    ts: datetime,
    lead_h: int,
    score: float,
    level: str,
    inputs: dict[str, Any],
    model_version: str,
) -> dict[str, Any]:
    return {
        "vineyard_id": vineyard_id,
        "block_id": block_id,
        "wedge": wedge,
        "ts": ts,
        "lead_h": lead_h,
        "score": float(score),
        "level": level,
        "inputs": json.dumps(inputs),
        "model_version": model_version,
    }


def _dsv_to_level(dsv: int) -> str:
    if dsv == 0:
        return "low"
    if dsv == 1:
        return "elevated"
    if dsv <= 3:
        return "high"
    return "extreme"


def _gt_index_to_level(idx: int) -> str:
    if idx < 30:
        return "low"
    if idx < 60:
        return "elevated"
    if idx < 80:
        return "high"
    return "extreme"


def _prob_to_level(p: float) -> str:
    if p < 0.20:
        return "low"
    if p < 0.50:
        return "elevated"
    if p < 0.85:
        return "high"
    return "extreme"
