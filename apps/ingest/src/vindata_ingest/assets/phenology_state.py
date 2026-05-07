"""Phenology state asset — populates ``phenology_state`` per block.

Re-computes the full season-to-date BBCH trace each cycle (idempotent;
fast at PoC volumes — ~200 days × 6 blocks × <1 ms each). The Caffarra-
Eccel model is per-cultivar, so we resolve cultivar → parameters via
``agronomy.phenology.params_for``.

Daily Tmin/Tmax come from rolling up the hourly ``weather_forecasts``
rows by calendar date. The model is timestep-agnostic (it accepts a list
of ``DailyTemps``); the season-start DOY anchors chill onset.
"""

from datetime import UTC, date, datetime
from typing import Any

import structlog
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from sqlalchemy import text

from agronomy import PHENOLOGY_MODEL_VERSION
from agronomy.phenology import (
    DailyTemps,
    caffarra_eccel_bbch,
    params_for,
)
from vindata_ingest.assets.curated_forecast import curated_forecast
from vindata_ingest.resources import PostgresResource

log = structlog.get_logger(__name__)

#: Southern-hemisphere viticultural season start: 1 May (DOY 121). Chill
#: accumulation is anchored from this date.
SEASON_START_DOY: int = 121


def _doy(d: date) -> int:
    return int(d.strftime("%j"))


@asset(
    name="phenology_state",
    group_name="score",
    deps=[curated_forecast],
    description=(
        "Per-block daily BBCH stage from Caffarra-Eccel chilling+forcing. "
        "Runs first in the score group so disease/smoke can read BBCH."
    ),
    compute_kind="python",
)
def phenology_state(
    context: AssetExecutionContext,
    postgres: PostgresResource,
) -> MaterializeResult:
    today = datetime.now(tz=UTC).date()

    # Daily rollup of forecast temperatures since season start. Uses the
    # most recent init_ts per (vineyard, valid_ts) — ON CONFLICT in the
    # forecast upsert means we always have the latest cycle's view.
    daily_sql = text("""
        SELECT vineyard_id,
               valid_ts::date AS d,
               min(t2m) FILTER (WHERE t2m IS NOT NULL) AS tmin,
               max(t2m) FILTER (WHERE t2m IS NOT NULL) AS tmax
        FROM weather_forecasts
        WHERE model = 'open_meteo'
          AND valid_ts >= make_date(EXTRACT(YEAR FROM CURRENT_DATE)::INT, 5, 1)
        GROUP BY vineyard_id, valid_ts::date
        ORDER BY vineyard_id, d
    """)
    blocks_sql = text("""
        SELECT id, vineyard_id, COALESCE(cultivar, 'Chardonnay') AS cultivar
        FROM blocks
        ORDER BY vineyard_id, id
    """)

    n_states = 0
    n_blocks = 0
    with postgres.session() as session:
        block_rows = session.execute(blocks_sql).all()
        daily_rows = session.execute(daily_sql).all()

        # Group daily rows by vineyard_id.
        per_vineyard: dict[int, list[tuple[date, float, float]]] = {}
        for vid, d, tmin, tmax in daily_rows:
            if tmin is None or tmax is None:
                continue
            per_vineyard.setdefault(vid, []).append((d, float(tmin), float(tmax)))

        for block_id, vineyard_id, cultivar in block_rows:
            series = per_vineyard.get(vineyard_id, [])
            if not series:
                continue
            n_blocks += 1
            params = params_for(cultivar)

            # Build the DailyTemps sequence; carry the dates so we can map
            # each PhenologyState back to a calendar date for upsert.
            dates = [d for (d, _, _) in series]
            days = [DailyTemps(tmin_c=tn, tmax_c=tx) for (_, tn, tx) in series]
            start_doy = _doy(dates[0])

            trace = caffarra_eccel_bbch(days, start_doy=start_doy, params=params)

            upsert_rows: list[dict[str, Any]] = []
            for d, state in zip(dates, trace.states, strict=True):
                if d > today:
                    # Don't materialise future rows — disease/smoke gates
                    # read "today's BBCH"; the trace will re-extend naturally
                    # next cycle as new forecast days roll in.
                    continue
                upsert_rows.append(
                    {
                        "block_id": block_id,
                        "date": d,
                        "doy": state.doy,
                        "chill_units": state.chill_units,
                        "forcing_dd": state.forcing_dd,
                        "gdd_from_budbreak": state.gdd_from_budbreak,
                        "bbch": int(state.bbch),
                        "model_version": PHENOLOGY_MODEL_VERSION,
                    }
                )
            if not upsert_rows:
                continue

            upsert_sql = text("""
                INSERT INTO phenology_state
                    (block_id, date, doy, chill_units, forcing_dd,
                     gdd_from_budbreak, bbch, model_version)
                VALUES
                    (:block_id, :date, :doy, :chill_units, :forcing_dd,
                     :gdd_from_budbreak, :bbch, :model_version)
                ON CONFLICT (block_id, date)
                DO UPDATE SET
                    doy = EXCLUDED.doy,
                    chill_units = EXCLUDED.chill_units,
                    forcing_dd = EXCLUDED.forcing_dd,
                    gdd_from_budbreak = EXCLUDED.gdd_from_budbreak,
                    bbch = EXCLUDED.bbch,
                    model_version = EXCLUDED.model_version
            """)
            session.execute(upsert_sql, upsert_rows)
            n_states += len(upsert_rows)

    return MaterializeResult(
        metadata={
            "blocks": MetadataValue.int(n_blocks),
            "states_written": MetadataValue.int(n_states),
            "model_version": MetadataValue.text(PHENOLOGY_MODEL_VERSION),
            "season_start_doy": MetadataValue.int(SEASON_START_DOY),
        }
    )
