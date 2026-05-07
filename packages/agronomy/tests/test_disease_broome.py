"""Broome 1995 botrytis-infection logistic tests."""

from __future__ import annotations

import pytest

from agronomy.disease.broome_botrytis import (
    botrytis_infection_probability,
    probability_to_level,
)


class TestBotrytisProbability:
    def test_short_event_lower_than_long(self) -> None:
        # The Broome 1995 logistic produces high probabilities even at
        # moderate (T, LWD) — what matters operationally is the *gap*
        # between a marginal event and a dangerous one.
        short = botrytis_infection_probability(t_mean_wet_c=15.0, lwd_hours=6.0)
        long_ = botrytis_infection_probability(t_mean_wet_c=15.0, lwd_hours=24.0)
        assert short.probability < long_.probability
        assert short.in_envelope

    def test_long_warm_event_high_probability(self) -> None:
        # 36 h wet at 22 °C → essentially certain infection on the
        # published logistic (Z >> 0).
        r = botrytis_infection_probability(t_mean_wet_c=22.0, lwd_hours=36.0)
        assert r.probability > 0.85
        assert r.in_envelope

    def test_outside_envelope_clamps_and_flags(self) -> None:
        r = botrytis_infection_probability(t_mean_wet_c=5.0, lwd_hours=10.0)
        assert not r.in_envelope
        # Still returns a value (clamped to 8 °C).
        assert 0.0 <= r.probability <= 1.0

    def test_short_dry_clamped(self) -> None:
        r = botrytis_infection_probability(t_mean_wet_c=18.0, lwd_hours=3.0)
        assert not r.in_envelope
        assert 0.0 <= r.probability <= 1.0

    def test_probability_increases_with_wet_duration(self) -> None:
        # Hold T constant; probability should rise with LWD.
        a = botrytis_infection_probability(t_mean_wet_c=20.0, lwd_hours=10.0).probability
        b = botrytis_infection_probability(t_mean_wet_c=20.0, lwd_hours=30.0).probability
        c = botrytis_infection_probability(t_mean_wet_c=20.0, lwd_hours=60.0).probability
        assert a <= b <= c


class TestLevelMapping:
    def test_bands(self) -> None:
        assert probability_to_level(0.10) == "low"
        assert probability_to_level(0.30) == "elevated"
        assert probability_to_level(0.70) == "high"
        assert probability_to_level(0.90) == "extreme"

    def test_boundary_values(self) -> None:
        assert probability_to_level(0.20) == "elevated"
        assert probability_to_level(0.85) == "extreme"


class TestProbabilityRange:
    @pytest.mark.parametrize("t,lwd", [(10, 12), (15, 24), (20, 36), (25, 48), (28, 70)])
    def test_in_unit_interval(self, t: float, lwd: float) -> None:
        p = botrytis_infection_probability(t, lwd).probability
        assert 0.0 <= p <= 1.0
