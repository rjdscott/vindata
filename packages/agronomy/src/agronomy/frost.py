"""Radiation-cooling frost prediction for vineyard blocks.

Implements a simplified FFST-style minimum-temperature predictor for clear,
calm conditions, after:

    Allen, L.H. (1957). A simple method of forecasting the minimum
    temperature.  Mon. Weather Rev. 85: 33-37.

    Snyder, R.L. and de Melo-Abreu, J.P. (2005). Frost protection:
    fundamentals, practice and economics. FAO Environment and Natural
    Resources Service Series, No. 10.

The model is intentionally simple at Stage 00: it uses the dewpoint as the
asymptotic minimum and reduces the cooling rate as cloud cover and wind speed
increase.  Coefficients are literature defaults; Stage 01 refits them on
five years of Orange AWS history (BoM 063303).

Public API (re-exported from ``agronomy.__init__``):

    - ``ForecastSample``  — one (T, Td, wind, cloud) sample at a valid time.
    - ``FrostParams``     — model coefficients, with sensible defaults.
    - ``predict_tmin``    — pure function: forecast → predicted minimum °C.
    - ``score_frost``     — pure function: predicted minimum → 0..1 score.
    - ``FrostScore``      — frozen dataclass: (score, level, tmin_c).
    - ``FrostLevel``      — enum: low / elevated / high / extreme.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import sqrt
from typing import Final

# ---------------------------------------------------------------------------
# Domain constants — visible at module level for testability.
# ---------------------------------------------------------------------------

#: Cap on wind speed used in the cooling-rate reduction term (m/s).
#: Above this, advective mixing dominates and the radiation model isn't valid;
#: we cap rather than clamp the score so the prediction degrades gracefully.
WIND_CAP_MS: Final[float] = 4.0

#: Score thresholds (predicted Tmin °C → frost level).  See ``score_frost``.
LEVEL_LOW_MAX: Final[float] = 0.25
LEVEL_ELEVATED_MAX: Final[float] = 0.50
LEVEL_HIGH_MAX: Final[float] = 0.75


class FrostLevel(StrEnum):
    """Discrete frost-risk bands shown to the user."""

    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass(frozen=True, slots=True)
class FrostParams:
    """Coefficients for the radiation-cooling Tmin model.

    Defaults are literature midpoints from Snyder & de Melo-Abreu (2005);
    they will be refit per-region in Stage 01.
    """

    #: Bulk cooling rate (°C / sqrt(hour)) at zero cloud and zero wind.
    k: float = 1.6
    #: Reduction factor for cloud cover (dimensionless, applied as 1 - c*cloud).
    c_cloud: float = 0.7
    #: Reduction factor for wind speed (per (m/s), applied as 1 - w*wind_capped).
    c_wind: float = 0.25
    #: Block-level cold-air drainage adjustment per percent of slope (°C/% slope).
    #: Applied only when ``stable_bl`` is true.  Negative because cold-sink blocks
    #: get *colder* than the open-field forecast.
    drainage_per_pct: float = -0.06


@dataclass(frozen=True, slots=True)
class ForecastSample:
    """One forecast sample feeding the Tmin prediction.

    All temperatures in °C; wind in m/s; cloud as a fraction in [0, 1];
    ``hours_since_sunset`` is the count of hours from local astronomical
    sunset to ``valid_ts``.
    """

    t2m_c: float
    dewpoint_c: float
    wind_ms: float
    cloud_frac: float
    hours_since_sunset: float

    def __post_init__(self) -> None:
        # Defensive validation at the data boundary.  The sample comes from
        # external sources and we'd rather fail fast than silently score on
        # nonsense.  Frozen dataclass requires using object.__setattr__ to
        # raise these as errors via __post_init__.
        if not -50.0 <= self.t2m_c <= 60.0:
            raise ValueError(f"t2m_c out of plausible range: {self.t2m_c}")
        if not -50.0 <= self.dewpoint_c <= self.t2m_c + 0.5:
            raise ValueError(
                f"dewpoint_c {self.dewpoint_c} must be ≤ t2m_c {self.t2m_c}"
            )
        if not 0.0 <= self.wind_ms <= 75.0:
            raise ValueError(f"wind_ms out of plausible range: {self.wind_ms}")
        if not 0.0 <= self.cloud_frac <= 1.0:
            raise ValueError(f"cloud_frac must be in [0,1]: {self.cloud_frac}")
        if self.hours_since_sunset < 0:
            raise ValueError(
                f"hours_since_sunset must be non-negative: {self.hours_since_sunset}"
            )


@dataclass(frozen=True, slots=True)
class FrostScore:
    """Output of ``score_frost``.  ``inputs`` mirrors the ForecastSample as a
    dict so it can be serialised straight into ``agronomy_scores.inputs``."""

    score: float
    level: FrostLevel
    tmin_c: float
    inputs: dict[str, float]


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------


def predict_tmin(
    sample: ForecastSample,
    params: FrostParams = FrostParams(),
    slope_pct: float = 0.0,
    stable_bl: bool = True,
) -> float:
    """Predict overnight minimum air temperature at 2 m, in °C.

    Args:
        sample: One forecast sample at a valid time (typically the predicted
            coldest hour, often near local sunrise).
        params: Model coefficients.
        slope_pct: Block slope in percent.  Applied via the cold-air drainage
            adjustment when ``stable_bl`` is true.  Defaults to 0 (flat).
        stable_bl: True when the boundary layer is stable (calm, clear), in
            which case cold-air drainage matters.  When false the drainage
            term is dropped.

    Returns:
        Predicted minimum air temperature (°C).

    Notes:
        Equation (Snyder & de Melo-Abreu 2005, §3):

            Tmin ≈ Td − k · sqrt(t) · (1 − c · cloud) · (1 − w · min(wind, W))

        with W being ``WIND_CAP_MS``.  When ``stable_bl`` is true we add the
        block-scale drainage adjustment ``drainage_per_pct · slope_pct`` (°C).

        We do **not** clamp the result — callers may want to inspect very low
        predictions (e.g. < −5 °C) directly.
    """
    wind_capped = min(sample.wind_ms, WIND_CAP_MS)
    cloud_term = 1.0 - params.c_cloud * sample.cloud_frac
    wind_term = 1.0 - params.c_wind * wind_capped
    cooling = params.k * sqrt(sample.hours_since_sunset) * cloud_term * wind_term
    tmin = sample.dewpoint_c - cooling
    if stable_bl:
        tmin += params.drainage_per_pct * slope_pct
    return tmin


def score_frost(tmin_c: float, sample: ForecastSample) -> FrostScore:
    """Map predicted Tmin to a 0..1 risk score with a discrete level.

    The score linearly interpolates between Tmin = +2 °C (no risk, score 0)
    and Tmin = −2 °C (extreme, score 1).  This bracket reflects the practical
    threshold band where bud / canopy frost damage transitions from possible
    to severe in cool-climate Australia.

    Level mapping (chosen to align with industry convention, e.g. NSW DPI
    frost advisories):

        score < 0.25  → low
        0.25 ≤ s < 0.50 → elevated
        0.50 ≤ s < 0.75 → high
        score ≥ 0.75  → extreme
    """
    raw = (2.0 - tmin_c) / 4.0
    score = max(0.0, min(1.0, raw))
    level = _level_from_score(score)
    return FrostScore(
        score=score,
        level=level,
        tmin_c=tmin_c,
        inputs={
            "t2m_c": sample.t2m_c,
            "dewpoint_c": sample.dewpoint_c,
            "wind_ms": sample.wind_ms,
            "cloud_frac": sample.cloud_frac,
            "hours_since_sunset": sample.hours_since_sunset,
        },
    )


def _level_from_score(score: float) -> FrostLevel:
    if score < LEVEL_LOW_MAX:
        return FrostLevel.LOW
    if score < LEVEL_ELEVATED_MAX:
        return FrostLevel.ELEVATED
    if score < LEVEL_HIGH_MAX:
        return FrostLevel.HIGH
    return FrostLevel.EXTREME
