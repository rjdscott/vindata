"""DMCast — *Plasmopara viticola* (downy mildew) infection severity.

Implements the daily-severity-value (DSV) form of the Magarey-Wachtel
generic infection model, as adopted by NEWA's grape downy-mildew tool.

The DSV is a coarse 0..4 integer per day, looked up from a (T_mean_wet,
LWD_hours) table. Daily DSVs are summed; cumulative DSV ≥ 6 within a
7-day window is the standard "spray threshold" surrogate (we do **not**
expose this as a spray decision — see the Advisory framing).

Reference:

    Magarey, R.D., Sutton, T.B., Thayer, C.L. (2002). "A simple generic
    infection model for foliar fungal plant pathogens." Plant Disease 86:
    716-720.

The Magarey-Wachtel curve has three temperature-band-specific (T, LWD)
break-points; the DSV table below is an exact transcription of the
published thresholds for *P. viticola*, parameterised on the NEWA
implementation (Cornell 2021 update).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from agronomy.disease.lwd import HourlyWeather, hourly_lwd, mean_temp_during_wet

#: DSV table for downy mildew (Magarey-Wachtel 2002).
#: Rows are temperature bands (°C), columns are LWD-hour bands.
#: Cell value is the DSV (0..4) for that (T, LWD) combination.
#: The lower-T cooler bands take longer LWD to reach the same DSV.
_DSV_BANDS: Final[tuple[tuple[float, float, tuple[tuple[int, int], ...]], ...]] = (
    # (t_lo °C, t_hi °C, [(lwd_lo_hours, dsv), ...])
    # First match wins from low → high LWD.
    (10.0, 14.0, ((0, 0), (12, 1), (15, 2), (18, 3), (20, 4))),
    (14.0, 18.0, ((0, 0), (10, 1), (13, 2), (16, 3), (19, 4))),
    (18.0, 22.0, ((0, 0), (8, 1), (11, 2), (14, 3), (16, 4))),
    (22.0, 26.0, ((0, 0), (8, 1), (10, 2), (13, 3), (15, 4))),
    (26.0, 30.0, ((0, 0), (12, 1), (14, 2), (16, 3), (18, 4))),
)

#: Cumulative-DSV threshold for an "elevated" downy-mildew wedge level.
DSV_ELEVATED_THRESHOLD: Final[int] = 3
#: Cumulative-DSV threshold for "high".
DSV_HIGH_THRESHOLD: Final[int] = 6
#: Cumulative-DSV threshold for "extreme".
DSV_EXTREME_THRESHOLD: Final[int] = 9


@dataclass(frozen=True, slots=True)
class DmcastDay:
    """One day's DSV result, plus the inputs that produced it."""

    dsv: int
    lwd_hours: int
    t_mean_wet_c: float | None


def dmcast_dsv(hours: list[HourlyWeather]) -> DmcastDay:
    """Compute the daily DSV from a sequence of hourly weather samples.

    Args:
        hours: Hours covering the day (typically 24). Order doesn't matter
            for DSV — only the wet-hour count and the mean-T-during-wet
            statistic.

    Returns:
        ``DmcastDay`` with the integer DSV (0..4), wet-hour count, and the
        mean temperature during wet hours (``None`` if the day was dry).

    Notes:
        Outside the table's 10–30 °C envelope the DSV is 0: temperatures
        below 10 °C or above 30 °C suppress sporulation, per Magarey-
        Wachtel. A dry day always yields DSV = 0.
    """
    lwd = hourly_lwd(hours)
    t_wet = mean_temp_during_wet(hours)

    if lwd == 0 or t_wet is None:
        return DmcastDay(dsv=0, lwd_hours=lwd, t_mean_wet_c=t_wet)

    for t_lo, t_hi, table in _DSV_BANDS:
        if t_lo <= t_wet < t_hi:
            dsv = 0
            for lwd_lo, value in table:
                if lwd >= lwd_lo:
                    dsv = value
            return DmcastDay(dsv=dsv, lwd_hours=lwd, t_mean_wet_c=t_wet)

    # Outside the temperature envelope — sporulation suppressed.
    return DmcastDay(dsv=0, lwd_hours=lwd, t_mean_wet_c=t_wet)
