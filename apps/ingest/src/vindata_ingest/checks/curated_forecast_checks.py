"""Asset checks for ``curated_forecast``.

Three independent invariants:

1. **No null core variables** — every row must have non-null
   ``t2m, dewpoint, wind_ms, cloud_frac``. These four are what
   ``frost_score`` consumes; a null silently degrades to "skipped" rather
   than erroring, which we'd rather surface as an asset-check failure.

2. **Temperatures in plausible range** — ``-30 °C ≤ t2m ≤ 50 °C`` and
   ``-30 °C ≤ dewpoint ≤ 50 °C``. Values outside this window indicate a
   unit conversion bug or a corrupt source response.

3. **valid_ts strictly monotone per (vineyard, init_ts)** — the forecast
   horizon must increase in time. A duplicate or out-of-order timestamp
   means an upsert collision or a bad source.

All three run on the most recent ``init_ts`` only; we don't re-check
historical chunks each materialisation.
"""

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetCheckSpec,
    asset_check,
)
from sqlalchemy import text

from vindata_ingest.assets.curated_forecast import curated_forecast
from vindata_ingest.resources import PostgresResource

_LATEST_CYCLE_FILTER = """
    init_ts = (SELECT max(init_ts) FROM weather_forecasts WHERE model='open_meteo')
"""


@asset_check(
    asset=curated_forecast,
    name="forecast_variables_not_null",
    description="t2m, dewpoint, wind_ms, cloud_frac all non-null in latest cycle.",
    blocking=True,
)
def forecast_variables_not_null(postgres: PostgresResource) -> AssetCheckResult:
    sql = text(
        f"""
        SELECT count(*) FROM weather_forecasts
        WHERE model = 'open_meteo' AND {_LATEST_CYCLE_FILTER}
          AND (t2m IS NULL OR dewpoint IS NULL
               OR wind_ms IS NULL OR cloud_frac IS NULL)
        """
    )
    with postgres.session() as session:
        nulls: int = session.execute(sql).scalar_one()
    return AssetCheckResult(
        passed=nulls == 0,
        severity=AssetCheckSeverity.ERROR,
        description=f"{nulls} rows in latest cycle have null core variables",
        metadata={"null_rows": nulls},
    )


@asset_check(
    asset=curated_forecast,
    name="forecast_temperatures_in_range",
    description="t2m and dewpoint within [-30, 50] °C in latest cycle.",
    blocking=True,
)
def forecast_temperatures_in_range(postgres: PostgresResource) -> AssetCheckResult:
    sql = text(
        f"""
        SELECT count(*) FROM weather_forecasts
        WHERE model = 'open_meteo' AND {_LATEST_CYCLE_FILTER}
          AND (t2m < -30 OR t2m > 50 OR dewpoint < -30 OR dewpoint > 50)
        """
    )
    with postgres.session() as session:
        oor: int = session.execute(sql).scalar_one()
    return AssetCheckResult(
        passed=oor == 0,
        severity=AssetCheckSeverity.ERROR,
        description=f"{oor} rows in latest cycle out of range",
        metadata={"out_of_range_rows": oor},
    )


@asset_check(
    asset=curated_forecast,
    name="forecast_valid_ts_monotone",
    description="valid_ts strictly increasing per (vineyard_id, init_ts) in latest cycle.",
    blocking=False,  # Warn-only: ordering issues are recoverable.
)
def forecast_valid_ts_monotone(postgres: PostgresResource) -> AssetCheckResult:
    # Use window function to find any consecutive pair where valid_ts <= prev.
    sql = text(
        f"""
        SELECT count(*) FROM (
            SELECT
                valid_ts,
                lag(valid_ts) OVER (
                    PARTITION BY vineyard_id, init_ts ORDER BY valid_ts
                ) AS prev_valid_ts
            FROM weather_forecasts
            WHERE model = 'open_meteo' AND {_LATEST_CYCLE_FILTER}
        ) t
        WHERE prev_valid_ts IS NOT NULL AND valid_ts <= prev_valid_ts
        """
    )
    with postgres.session() as session:
        violations: int = session.execute(sql).scalar_one()
    return AssetCheckResult(
        passed=violations == 0,
        severity=AssetCheckSeverity.WARN,
        description=f"{violations} non-monotone valid_ts pairs",
        metadata={"violations": violations},
    )


# Re-exported for the Definitions object.
ALL_CHECKS: list[AssetCheckSpec] = []  # type: ignore[var-annotated]
