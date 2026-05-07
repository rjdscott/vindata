"""Tests for ``agronomy.frost``.

Three layers:

  1. **Boundary-validation tests** — confirm ``ForecastSample`` rejects
     out-of-range inputs at the data boundary, before any model runs.

  2. **Property tests (hypothesis)** — confirm structural invariants:
     score is always in [0, 1]; score is monotone non-increasing in
     predicted Tmin; level-from-score boundaries are consistent.

  3. **Golden-vector tests** — three hand-computed cases against the model
     equation, ensuring the implementation matches the literature form.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from agronomy.frost import (
    LEVEL_ELEVATED_MAX,
    LEVEL_HIGH_MAX,
    LEVEL_LOW_MAX,
    WIND_CAP_MS,
    ForecastSample,
    FrostLevel,
    FrostParams,
    predict_tmin,
    score_frost,
)

# ---------------------------------------------------------------------------
# Boundary validation
# ---------------------------------------------------------------------------


class TestForecastSampleValidation:
    def test_rejects_dewpoint_above_t2m(self) -> None:
        with pytest.raises(ValueError, match="dewpoint_c"):
            ForecastSample(
                t2m_c=5.0,
                dewpoint_c=10.0,
                wind_ms=1.0,
                cloud_frac=0.1,
                hours_since_sunset=6.0,
            )

    def test_rejects_negative_wind(self) -> None:
        with pytest.raises(ValueError, match="wind_ms"):
            ForecastSample(
                t2m_c=5.0,
                dewpoint_c=2.0,
                wind_ms=-1.0,
                cloud_frac=0.1,
                hours_since_sunset=6.0,
            )

    def test_rejects_cloud_outside_unit_interval(self) -> None:
        with pytest.raises(ValueError, match="cloud_frac"):
            ForecastSample(
                t2m_c=5.0,
                dewpoint_c=2.0,
                wind_ms=1.0,
                cloud_frac=1.5,
                hours_since_sunset=6.0,
            )

    def test_rejects_negative_hours_since_sunset(self) -> None:
        with pytest.raises(ValueError, match="hours_since_sunset"):
            ForecastSample(
                t2m_c=5.0,
                dewpoint_c=2.0,
                wind_ms=1.0,
                cloud_frac=0.1,
                hours_since_sunset=-1.0,
            )


# ---------------------------------------------------------------------------
# Hypothesis property tests
# ---------------------------------------------------------------------------

# A safe forecast strategy: dewpoint always ≤ t2m, wind/cloud/hours valid.
_t2m = st.floats(min_value=-20.0, max_value=40.0, allow_nan=False, allow_infinity=False)
_wind = st.floats(min_value=0.0, max_value=15.0, allow_nan=False, allow_infinity=False)
_cloud = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
_hours = st.floats(min_value=0.0, max_value=14.0, allow_nan=False, allow_infinity=False)
_dew_offset = st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)


@st.composite
def _samples(draw: st.DrawFn) -> ForecastSample:
    t = draw(_t2m)
    return ForecastSample(
        t2m_c=t,
        dewpoint_c=t - draw(_dew_offset),
        wind_ms=draw(_wind),
        cloud_frac=draw(_cloud),
        hours_since_sunset=draw(_hours),
    )


@given(sample=_samples())
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=200)
def test_score_in_unit_interval(sample: ForecastSample) -> None:
    tmin = predict_tmin(sample)
    out = score_frost(tmin, sample)
    assert 0.0 <= out.score <= 1.0


@given(tmin=st.floats(min_value=-15.0, max_value=10.0, allow_nan=False, allow_infinity=False))
def test_score_monotone_non_increasing_in_tmin(tmin: float) -> None:
    """Colder predicted Tmin must produce a *higher* score (or equal at the
    saturation extremes)."""
    sample = ForecastSample(
        t2m_c=10.0, dewpoint_c=5.0, wind_ms=1.0, cloud_frac=0.0, hours_since_sunset=6.0
    )
    a = score_frost(tmin, sample).score
    b = score_frost(tmin - 1.0, sample).score
    assert b >= a


@given(sample=_samples())
def test_predicted_tmin_never_above_dewpoint_with_drainage_off(sample: ForecastSample) -> None:
    """Without drainage, the cooling term is non-negative ⇒ Tmin ≤ Td."""
    tmin = predict_tmin(sample, slope_pct=0.0, stable_bl=False)
    assert tmin <= sample.dewpoint_c + 1e-9


# ---------------------------------------------------------------------------
# Golden vectors — hand-checked against the documented equation
# ---------------------------------------------------------------------------


class TestGoldenVectors:
    """Three reference cases.

    These pin the model: any change to coefficients or equation form will
    fail these and force a SemVer bump on ``FROST_MODEL_VERSION``.
    """

    PARAMS = FrostParams()  # default coefficients

    def test_clear_calm_six_hours(self) -> None:
        sample = ForecastSample(
            t2m_c=4.0,
            dewpoint_c=0.0,
            wind_ms=0.0,
            cloud_frac=0.0,
            hours_since_sunset=6.0,
        )
        # Tmin = 0 - 1.6*sqrt(6)*(1)*(1) = -3.918...
        expected = 0.0 - self.PARAMS.k * math.sqrt(6.0)
        assert math.isclose(predict_tmin(sample, self.PARAMS), expected, rel_tol=1e-9)

    def test_overcast_kills_cooling(self) -> None:
        sample = ForecastSample(
            t2m_c=4.0,
            dewpoint_c=0.0,
            wind_ms=0.0,
            cloud_frac=1.0,
            hours_since_sunset=6.0,
        )
        # cloud_term = 1 - 0.7*1 = 0.3
        expected = 0.0 - self.PARAMS.k * math.sqrt(6.0) * 0.3
        assert math.isclose(predict_tmin(sample, self.PARAMS), expected, rel_tol=1e-9)

    def test_wind_above_cap_clamps(self) -> None:
        below = ForecastSample(
            t2m_c=4.0, dewpoint_c=0.0, wind_ms=WIND_CAP_MS,
            cloud_frac=0.0, hours_since_sunset=6.0,
        )
        above = ForecastSample(
            t2m_c=4.0, dewpoint_c=0.0, wind_ms=WIND_CAP_MS + 5.0,
            cloud_frac=0.0, hours_since_sunset=6.0,
        )
        assert math.isclose(
            predict_tmin(below, self.PARAMS),
            predict_tmin(above, self.PARAMS),
            rel_tol=1e-9,
        )

    def test_drainage_makes_low_blocks_colder(self) -> None:
        sample = ForecastSample(
            t2m_c=4.0,
            dewpoint_c=0.0,
            wind_ms=0.0,
            cloud_frac=0.0,
            hours_since_sunset=6.0,
        )
        flat = predict_tmin(sample, self.PARAMS, slope_pct=0.0, stable_bl=True)
        sloped = predict_tmin(sample, self.PARAMS, slope_pct=10.0, stable_bl=True)
        # 10% slope with default drainage_per_pct=-0.06 ⇒ -0.6 °C
        assert math.isclose(sloped, flat - 0.6, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Level mapping
# ---------------------------------------------------------------------------


class TestLevelBoundaries:
    SAMPLE = ForecastSample(
        t2m_c=4.0, dewpoint_c=0.0, wind_ms=0.0, cloud_frac=0.0, hours_since_sunset=6.0
    )

    @pytest.mark.parametrize(
        ("tmin", "expected_level"),
        [
            (5.0, FrostLevel.LOW),       # score = 0 → low
            (1.5, FrostLevel.LOW),       # score = 0.125 → low
            (0.5, FrostLevel.ELEVATED),  # score = 0.375 → elevated
            (-0.5, FrostLevel.HIGH),     # score = 0.625 → high
            (-2.0, FrostLevel.EXTREME),  # score = 1.0 → extreme
        ],
    )
    def test_level_mapping(self, tmin: float, expected_level: FrostLevel) -> None:
        assert score_frost(tmin, self.SAMPLE).level == expected_level

    def test_thresholds_consistent(self) -> None:
        # Sanity: thresholds increase strictly low < elevated < high < 1.
        assert 0.0 < LEVEL_LOW_MAX < LEVEL_ELEVATED_MAX < LEVEL_HIGH_MAX < 1.0
