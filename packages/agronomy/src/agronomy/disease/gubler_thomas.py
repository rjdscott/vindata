"""Gubler-Thomas powdery-mildew Risk Index.

Implements the UC IPM 1999 daily Risk Index for *Erysiphe necator* on
*Vitis vinifera*. The model rewards consecutive 6-h blocks with T in the
optimum 21–30 °C band (+20 points each, capped at +60/day) and penalises
days with T > 35 °C (-10 points). Days outside the band get -10. Index is
clamped to [0, 100] and reset back toward 0 by 10/day on penalty days.

Reference:

    Gubler, W.D., Rademacher, M.R., Vasquez, S.J. (1999). "Control of
    powdery mildew using the UC Davis powdery mildew risk index."
    APSnet Features. UC IPM Pest Management Guidelines: Grape.

The model is gated on BBCH ≥ 53 (inflorescences swelling); pre-flowering
days are skipped entirely. Callers handle the BBCH gate before calling
``gubler_thomas_step``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from agronomy.disease.lwd import HourlyWeather

#: Optimum band for sporulation (°C).
OPTIMUM_T_LO: Final[float] = 21.0
OPTIMUM_T_HI: Final[float] = 30.0
#: Lethal-temperature threshold above which the index drops (°C).
LETHAL_T: Final[float] = 35.0

#: Per 6-h-block reward / per-day daily penalty.
REWARD_PER_BLOCK: Final[int] = 20
DAILY_PENALTY: Final[int] = -10
#: Index bounds (UC IPM table).
INDEX_MIN: Final[int] = 0
INDEX_MAX: Final[int] = 100
#: Maximum reward per day (caps at three 6-h blocks).
MAX_DAILY_REWARD: Final[int] = 3 * REWARD_PER_BLOCK

#: Risk-level thresholds (matches UC IPM extension publications).
LEVEL_LOW_MAX: Final[int] = 30
LEVEL_ELEVATED_MAX: Final[int] = 60
LEVEL_HIGH_MAX: Final[int] = 80


@dataclass(frozen=True, slots=True)
class GublerThomasDay:
    """One day's index update."""

    new_index: int
    delta: int
    optimum_blocks: int
    had_lethal: bool


def _count_optimum_blocks(hours: list[HourlyWeather]) -> int:
    """Count consecutive 6-h blocks where every hour is in the optimum band."""
    if len(hours) < 6:
        return 0
    blocks = 0
    # Walk non-overlapping 6-h windows.
    for i in range(0, len(hours) - 5, 6):
        window = hours[i : i + 6]
        if all(OPTIMUM_T_LO <= h.t2m_c <= OPTIMUM_T_HI for h in window):
            blocks += 1
    return blocks


def _had_lethal(hours: list[HourlyWeather]) -> bool:
    """True if any hour exceeds the lethal threshold."""
    return any(h.t2m_c > LETHAL_T for h in hours)


def gubler_thomas_index(
    hours: list[HourlyWeather],
    prior_index: int = 0,
) -> GublerThomasDay:
    """Step the Gubler-Thomas index by one day.

    Args:
        hours: 24 ordered hourly samples for the day.
        prior_index: Yesterday's index (start with 0 at season start).

    Returns:
        ``GublerThomasDay`` with the new clamped index, the delta applied,
        the count of qualifying 6-h blocks, and whether a lethal hour was
        observed.

    Notes:
        Per UC IPM, a single day with > 35 °C drops the index back toward
        zero (the -10 daily penalty). Three full 6-h optimum blocks yield
        the +60 daily ceiling. The index is **monotone-bounded** in [0,
        100] — it cannot run away.
    """
    blocks = _count_optimum_blocks(hours)
    lethal = _had_lethal(hours)

    reward = min(blocks * REWARD_PER_BLOCK, MAX_DAILY_REWARD)
    delta: int
    if lethal:
        delta = DAILY_PENALTY
    elif blocks > 0:
        delta = reward
    else:
        delta = DAILY_PENALTY

    new_index = max(INDEX_MIN, min(INDEX_MAX, prior_index + delta))
    return GublerThomasDay(
        new_index=new_index, delta=delta, optimum_blocks=blocks, had_lethal=lethal
    )


def index_to_level(index: int) -> str:
    """Map a Gubler-Thomas index to a wedge level (low/elevated/high/extreme)."""
    if index < LEVEL_LOW_MAX:
        return "low"
    if index < LEVEL_ELEVATED_MAX:
        return "elevated"
    if index < LEVEL_HIGH_MAX:
        return "high"
    return "extreme"
