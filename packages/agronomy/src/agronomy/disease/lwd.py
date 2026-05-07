"""Leaf Wetness Duration (LWD) — NEWA CART proxy.

Until our pilot vineyards have leaf-wetness sensors, LWD is estimated from
hourly weather. The CART (Classification And Regression Tree) rule used by
the Cornell NEWA network is the literature standard:

    A 1 h period is "wet" iff
        RH ≥ 90 %  OR  precip > 0.2 mm/h  OR  dewpoint depression ≤ 1.5 °C

The third clause picks up dew on still, clear, near-dewpoint nights that the
RH-only rule misses when 2-m RH lags surface RH.

Reference:

    Gleason, M.L. et al. (1994). "Disease-warning systems for processing
    tomatoes in eastern North America: are we there yet?" Plant Dis. 78:
    1027-1032 (CART rule, generalised in NEWA).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

#: NEWA CART thresholds. Public for tests / sensitivity analyses.
RH_WET_THRESHOLD: Final[float] = 90.0  # percent
PRECIP_WET_THRESHOLD_MM: Final[float] = 0.2
DEWPOINT_DEPRESSION_THRESHOLD_C: Final[float] = 1.5


@dataclass(frozen=True, slots=True)
class HourlyWeather:
    """One hour of forecast or observed weather feeding the LWD proxy.

    All fields use the API shape — RH as a percentage 0..100, not a fraction
    — to avoid silent unit mismatches with Open-Meteo. Precip in mm/h.
    """

    t2m_c: float
    dewpoint_c: float
    rh_pct: float
    precip_mm: float

    def __post_init__(self) -> None:
        if not -50.0 <= self.t2m_c <= 60.0:
            raise ValueError(f"t2m_c out of range: {self.t2m_c}")
        if not 0.0 <= self.rh_pct <= 100.0:
            raise ValueError(f"rh_pct must be in [0,100]: {self.rh_pct}")
        if self.precip_mm < 0:
            raise ValueError(f"precip_mm must be >= 0: {self.precip_mm}")
        if self.dewpoint_c > self.t2m_c + 0.5:
            raise ValueError(
                f"dewpoint_c {self.dewpoint_c} cannot exceed t2m_c {self.t2m_c}"
            )


def is_wet_hour(h: HourlyWeather) -> bool:
    """True iff this hour qualifies as wet under NEWA CART."""
    if h.rh_pct >= RH_WET_THRESHOLD:
        return True
    if h.precip_mm > PRECIP_WET_THRESHOLD_MM:
        return True
    return (h.t2m_c - h.dewpoint_c) <= DEWPOINT_DEPRESSION_THRESHOLD_C


def hourly_lwd(hours: list[HourlyWeather]) -> int:
    """Total wet-hour count over a sequence (hours). Empty list → 0."""
    return sum(1 for h in hours if is_wet_hour(h))


def mean_temp_during_wet(hours: list[HourlyWeather]) -> float | None:
    """Mean T during wet hours (°C); ``None`` if no wet hours.

    DMCast and Broome both score by (T_mean_wet, LWD); pulling this out
    once avoids walking the sequence twice.
    """
    wet = [h.t2m_c for h in hours if is_wet_hour(h)]
    if not wet:
        return None
    return sum(wet) / len(wet)
