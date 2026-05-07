"""Growing Degree Day accumulators.

Two seasonally relevant variants:

  * Winkler (1944) GDD with base 10 °C, no upper cap. Used to classify
    regions on the Winkler scale and to drive a cumulative thermal-time
    budget from budbreak onwards.

  * Huglin (1978) heliothermal index, which weights the day-length factor
    of latitude — a better predictor of sugar accumulation in cool-climate
    sites at high latitudes than plain Winkler.

References:

    Winkler, A.J. (1944). General Viticulture. UC Press.
    Hall, A. and Jones, G.V. (2010). "Spatial analysis of climate in
        winegrape growing regions in Australia." AJGWR 16: 389-404.
    Huglin, P. (1978). Comptes Rendus Acad. Agric. France 64: 1117-1126.

All inputs are daily aggregates (Tmin, Tmax, in °C). All functions are pure;
no globals; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Final

#: Standard Winkler base temperature (°C) for *Vitis vinifera*.
WINKLER_BASE_C: Final[float] = 10.0
#: Standard Huglin base temperature (°C). Identical to Winkler in practice;
#: kept as a separate constant so a future calibration can diverge them.
HUGLIN_BASE_C: Final[float] = 10.0


@dataclass(frozen=True, slots=True)
class DailyTemps:
    """One day's air-temperature summary.

    The minimal contract for both GDD variants: daily minimum and maximum
    in °C. We deliberately don't carry a date — accumulators are timestep
    agnostic, callers pair days with dates externally if they need to.
    """

    tmin_c: float
    tmax_c: float

    def __post_init__(self) -> None:
        if not -50.0 <= self.tmin_c <= 60.0:
            raise ValueError(f"tmin_c out of range: {self.tmin_c}")
        if not self.tmin_c <= self.tmax_c <= 60.0:
            raise ValueError(f"tmax_c {self.tmax_c} must be >= tmin_c {self.tmin_c}")

    @property
    def tmean_c(self) -> float:
        """Daily mean from min/max average — the standard agronomy proxy
        for true 24h mean when only Tn/Tx are available."""
        return (self.tmin_c + self.tmax_c) / 2.0


def winkler_gdd(day: DailyTemps, base_c: float = WINKLER_BASE_C) -> float:
    """Single-day Winkler GDD contribution (°C·d).

    Definition::

        GDD = max(0, ((Tmax + Tmin) / 2) - base)

    The "no upper cap" form is the convention used in the Australian
    classification work (Hall & Jones 2010); upper-cap variants exist
    (e.g., FAO 30 °C cap) but are not used here.
    """
    return max(0.0, day.tmean_c - base_c)


def huglin_index_day(
    day: DailyTemps, latitude_deg: float, base_c: float = HUGLIN_BASE_C
) -> float:
    """Single-day Huglin heliothermal index contribution (°C·d).

    Definition (Huglin 1978)::

        HI_day = K(lat) * ((Tmean - base) + (Tmax - base)) / 2

    with day-length coefficient ``K`` interpolated by latitude. The latitude
    input is signed: negative for southern hemisphere. We take ``abs(lat)``
    for the K lookup since the coefficient is symmetric about the equator.
    Outside ±50° the index is undefined; we clamp to the boundary K.
    """
    abs_lat = min(50.0, abs(latitude_deg))
    k = _huglin_k(abs_lat)
    contrib = ((day.tmean_c - base_c) + (day.tmax_c - base_c)) / 2.0
    return max(0.0, k * contrib)


# Huglin's published K coefficients (linearly interpolated between the
# table values from Huglin 1978, valid 40-50 deg absolute latitude; for
# lower latitudes K saturates at 1.02).
_HUGLIN_K_TABLE: Final[tuple[tuple[float, float], ...]] = (
    (40.0, 1.02),
    (42.0, 1.05),
    (44.0, 1.06),
    (46.0, 1.07),
    (48.0, 1.08),
    (50.0, 1.10),
)


def _huglin_k(abs_lat_deg: float) -> float:
    if abs_lat_deg <= _HUGLIN_K_TABLE[0][0]:
        return _HUGLIN_K_TABLE[0][1]
    for (lat_lo, k_lo), (lat_hi, k_hi) in pairwise(_HUGLIN_K_TABLE):
        if lat_lo <= abs_lat_deg <= lat_hi:
            t = (abs_lat_deg - lat_lo) / (lat_hi - lat_lo)
            return k_lo + t * (k_hi - k_lo)
    return _HUGLIN_K_TABLE[-1][1]


def cumulative_winkler(days: list[DailyTemps], base_c: float = WINKLER_BASE_C) -> float:
    """Sum daily Winkler GDD over a sequence (°C·d). Empty list → 0.0."""
    return sum(winkler_gdd(d, base_c) for d in days)
