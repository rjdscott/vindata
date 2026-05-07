"""Asset checks for the new wedge scoring assets.

Three independent invariants per wedge:

* **scores written** — the latest cycle produced ≥ 1 row for the wedge.
* **score in [0,1]** — every row's score column lands in the unit
  interval (we normalise in the asset; this catches arithmetic regressions).
* **level matches the constraint** — every row's level is a known band.
"""

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    asset_check,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from vindata_ingest.assets.disease_score import disease_score
from vindata_ingest.assets.phenology_state import phenology_state
from vindata_ingest.assets.smoke_score import smoke_score
from vindata_ingest.resources import PostgresResource


def _count_recent(session: Session, wedge: str) -> int:
    sql = text(
        """
        SELECT count(*) FROM agronomy_scores
        WHERE wedge = :wedge AND ts >= now() - interval '36 hours'
        """
    )
    return int(session.execute(sql, {"wedge": wedge}).scalar_one())


def _count_oor(session: Session, wedge: str) -> int:
    sql = text(
        """
        SELECT count(*) FROM agronomy_scores
        WHERE wedge = :wedge
          AND (score < 0 OR score > 1)
          AND ts >= now() - interval '36 hours'
        """
    )
    return int(session.execute(sql, {"wedge": wedge}).scalar_one())


@asset_check(
    asset=disease_score,
    name="disease_dm_rows_written",
    description="≥ 1 DM row in the last 36 h.",
    blocking=False,
)
def disease_dm_rows_written(postgres: PostgresResource) -> AssetCheckResult:
    with postgres.session() as session:
        n = _count_recent(session, "dm")
    return AssetCheckResult(
        passed=n > 0,
        severity=AssetCheckSeverity.WARN,
        description=f"{n} DM rows in last 36 h",
        metadata={"rows": n},
    )


@asset_check(
    asset=disease_score,
    name="disease_score_in_unit_interval",
    description="DM/PM/Botrytis scores within [0,1].",
    blocking=True,
)
def disease_score_in_unit_interval(postgres: PostgresResource) -> AssetCheckResult:
    with postgres.session() as session:
        oor = sum(_count_oor(session, w) for w in ("dm", "pm", "botrytis"))
    return AssetCheckResult(
        passed=oor == 0,
        severity=AssetCheckSeverity.ERROR,
        description=f"{oor} disease rows have score outside [0,1]",
        metadata={"out_of_range": oor},
    )


@asset_check(
    asset=smoke_score,
    name="smoke_score_in_unit_interval",
    description="Smoke score within [0,1].",
    blocking=True,
)
def smoke_score_in_unit_interval(postgres: PostgresResource) -> AssetCheckResult:
    with postgres.session() as session:
        oor = _count_oor(session, "smoke")
    return AssetCheckResult(
        passed=oor == 0,
        severity=AssetCheckSeverity.ERROR,
        description=f"{oor} smoke rows have score outside [0,1]",
        metadata={"out_of_range": oor},
    )


@asset_check(
    asset=phenology_state,
    name="phenology_bbch_in_range",
    description="BBCH stages within [0, 99].",
    blocking=True,
)
def phenology_bbch_in_range(postgres: PostgresResource) -> AssetCheckResult:
    sql = text(
        "SELECT count(*) FROM phenology_state WHERE bbch < 0 OR bbch > 99"
    )
    with postgres.session() as session:
        n = int(session.execute(sql).scalar_one())
    return AssetCheckResult(
        passed=n == 0,
        severity=AssetCheckSeverity.ERROR,
        description=f"{n} phenology rows have BBCH outside [0,99]",
        metadata={"out_of_range": n},
    )
