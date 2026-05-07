"""Caffarra-Eccel chilling+forcing phenology model.

Two-phase serial model: dormancy (chilling accumulation) until a critical
chill state ``C_crit`` is reached, after which the bud accumulates forcing
units (a thermal-time integrator) until budbreak (BBCH 9). Subsequent
stages (BBCH 65 flowering, BBCH 81 veraison, BBCH 89 maturity) are reached
via cumulative GDD from budbreak.

Reference:

    Caffarra, A. and Eccel, E. (2010). "Increasing the robustness of
    phenological models for *Vitis vinifera* cv. Chardonnay." Int. J.
    Biometeorol. 54: 255–267.

The published Chardonnay parameters are exposed as defaults; callers can
provide cultivar-specific overrides via ``CaffarraEccelParams``.

Inputs: a sequence of ``DailyTemps`` ordered by date (earliest first), and
the date-of-year (DOY) of the *first* element so the chilling onset can be
positioned correctly.

Outputs:

  * ``PhenologyTrace`` — the full state evolution (chill / forcing / GDD)
  * Stage transitions: budbreak DOY, flowering DOY, veraison DOY, maturity
    DOY (or ``None`` if not reached within the input window).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final

from agronomy.phenology.gdd import DailyTemps, winkler_gdd


class BBCH(IntEnum):
    """BBCH stages we track (subset)."""

    DORMANT = 0
    BUDBREAK = 9
    FLOWERING = 65
    VERAISON = 81
    MATURITY = 89


@dataclass(frozen=True, slots=True)
class CaffarraEccelParams:
    """Cultivar-specific chilling+forcing parameters.

    Defaults are Chardonnay (Caffarra & Eccel 2010, Table 2). Stage 01
    refits per-cultivar on Australian data; for now Shiraz uses the same
    parameters with a 10% higher forcing requirement (industry rule of
    thumb for late-budbreak cultivars in Orange).
    """

    #: Chill-window low (°C). Below this, the day contributes no chill.
    chill_t_lo: float = 0.0
    #: Chill-window high (°C). Above this, no chill accumulation.
    chill_t_hi: float = 7.5
    #: Critical chill units (chill-days) required to release dormancy.
    chill_crit: float = 60.0

    #: Forcing base temperature (°C). Below it, no forcing accumulates.
    force_base_c: float = 5.0
    #: Critical forcing thermal time to budbreak (°C·d).
    force_crit: float = 240.0

    #: GDD-from-budbreak (base 10 °C) thresholds for downstream stages.
    gdd_to_flowering: float = 350.0
    gdd_to_veraison: float = 1100.0
    gdd_to_maturity: float = 1450.0


CHARDONNAY: Final[CaffarraEccelParams] = CaffarraEccelParams()
SHIRAZ: Final[CaffarraEccelParams] = CaffarraEccelParams(
    force_crit=265.0, gdd_to_veraison=1180.0, gdd_to_maturity=1520.0
)
PINOT_NOIR: Final[CaffarraEccelParams] = CaffarraEccelParams(
    force_crit=220.0, gdd_to_flowering=320.0, gdd_to_maturity=1380.0
)

#: Lookup by cultivar name (lowercase). Unknown cultivars fall back to
#: Chardonnay parameters — documented in the seed migration.
CULTIVAR_PARAMS: Final[dict[str, CaffarraEccelParams]] = {
    "chardonnay": CHARDONNAY,
    "shiraz": SHIRAZ,
    "syrah": SHIRAZ,
    "pinot noir": PINOT_NOIR,
}


def params_for(cultivar: str | None) -> CaffarraEccelParams:
    """Resolve cultivar string to parameters, defaulting to Chardonnay."""
    if cultivar is None:
        return CHARDONNAY
    return CULTIVAR_PARAMS.get(cultivar.strip().lower(), CHARDONNAY)


@dataclass(frozen=True, slots=True)
class PhenologyState:
    """Snapshot of the phenology state on one day."""

    doy: int
    chill_units: float
    forcing_dd: float
    gdd_from_budbreak: float
    bbch: BBCH


@dataclass(frozen=True, slots=True)
class PhenologyTrace:
    """Complete day-by-day state plus stage transitions."""

    states: list[PhenologyState]
    budbreak_doy: int | None = field(default=None)
    flowering_doy: int | None = field(default=None)
    veraison_doy: int | None = field(default=None)
    maturity_doy: int | None = field(default=None)


def _chill_contribution(day: DailyTemps, params: CaffarraEccelParams) -> float:
    """Chill units for one day: 1.0 if Tmean is in the chill window, else 0.

    This is the simplified "chill-days" form used in many viticulture
    extensions. Caffarra & Eccel use a continuous logistic; the discrete
    form is within ~5% over a season and avoids carrying a parameter we
    can't yet calibrate. Stage 01 swaps in the continuous form once we
    have Orange AWS data to fit it on.
    """
    if params.chill_t_lo <= day.tmean_c <= params.chill_t_hi:
        return 1.0
    return 0.0


def _forcing_contribution(day: DailyTemps, params: CaffarraEccelParams) -> float:
    """Forcing thermal-time for one day (°C·d, base ``force_base_c``)."""
    return max(0.0, day.tmean_c - params.force_base_c)


def caffarra_eccel_bbch(  # noqa: PLR0912 — stage transitions naturally branch
    days: list[DailyTemps],
    start_doy: int,
    params: CaffarraEccelParams = CHARDONNAY,
) -> PhenologyTrace:
    """Walk a daily sequence through the chilling → forcing → GDD pipeline.

    Args:
        days: Ordered daily Tmin/Tmax. Index 0 is ``start_doy``.
        start_doy: Day-of-year of ``days[0]`` (1..366).
        params: Cultivar parameters. Defaults to Chardonnay.

    Returns:
        ``PhenologyTrace`` with one ``PhenologyState`` per input day plus
        the DOYs at which each BBCH transition occurred (``None`` if the
        sequence ended before the threshold was crossed).

    Notes:
        Chilling accumulates immediately; the forcing register only starts
        after ``chill_crit`` is reached (serial coupling). DOY wraps at
        366 → 1 transparently — callers feeding a multi-year window should
        pass DOY relative to the season start (e.g., 1 = 1 May SH for the
        2025 vintage).
    """
    if not days:
        return PhenologyTrace(states=[])

    chill = 0.0
    forcing = 0.0
    gdd_post = 0.0
    current = BBCH.DORMANT

    states: list[PhenologyState] = []
    bb_doy: int | None = None
    fl_doy: int | None = None
    ve_doy: int | None = None
    mt_doy: int | None = None

    for i, day in enumerate(days):
        doy = ((start_doy - 1 + i) % 366) + 1

        if current is BBCH.DORMANT:
            chill += _chill_contribution(day, params)
            if chill >= params.chill_crit:
                # Same-day rollover into forcing accumulation. We *do* let
                # the same day add a forcing increment because the bud is
                # released mid-day; this matches the published formulation.
                forcing += _forcing_contribution(day, params)
                if forcing >= params.force_crit:
                    current = BBCH.BUDBREAK
                    bb_doy = doy
        elif current is BBCH.BUDBREAK:
            forcing += _forcing_contribution(day, params)
            if forcing >= params.force_crit and bb_doy is None:
                bb_doy = doy
            # Once budbreak is logged, start the GDD-from-budbreak counter.
            if bb_doy is not None:
                gdd_post += winkler_gdd(day)
                if gdd_post >= params.gdd_to_flowering:
                    current = BBCH.FLOWERING
                    fl_doy = doy
        elif current is BBCH.FLOWERING:
            gdd_post += winkler_gdd(day)
            if gdd_post >= params.gdd_to_veraison:
                current = BBCH.VERAISON
                ve_doy = doy
        elif current is BBCH.VERAISON:
            gdd_post += winkler_gdd(day)
            if gdd_post >= params.gdd_to_maturity:
                current = BBCH.MATURITY
                mt_doy = doy
        elif current is BBCH.MATURITY:
            gdd_post += winkler_gdd(day)

        # Pre-budbreak window: still adding chill or forcing? After chill
        # crit but before forcing crit, accumulate forcing.
        if (
            current is BBCH.DORMANT
            and chill >= params.chill_crit
            and forcing < params.force_crit
        ):
            forcing += _forcing_contribution(day, params)
            if forcing >= params.force_crit:
                current = BBCH.BUDBREAK
                bb_doy = doy

        states.append(
            PhenologyState(
                doy=doy,
                chill_units=chill,
                forcing_dd=forcing,
                gdd_from_budbreak=gdd_post,
                bbch=current,
            )
        )

    return PhenologyTrace(
        states=states,
        budbreak_doy=bb_doy,
        flowering_doy=fl_doy,
        veraison_doy=ve_doy,
        maturity_doy=mt_doy,
    )
