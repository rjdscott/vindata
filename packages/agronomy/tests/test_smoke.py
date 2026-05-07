"""Smoke-taint dose model tests."""

from __future__ import annotations

import pytest

from agronomy.phenology.caffarra_eccel import BBCH
from agronomy.smoke import (
    LEVEL_ELEVATED_MAX,
    LEVEL_HIGH_MAX,
    LEVEL_LOW_MAX,
    HourlyExposure,
    phenology_weight,
    smoke_dose_index,
)


def _hour(pm: float, stab: str = "neutral") -> HourlyExposure:
    return HourlyExposure(pm25_ug_m3=pm, stability=stab)


class TestHourlyExposure:
    def test_validates_negative(self) -> None:
        with pytest.raises(ValueError, match="pm25_ug_m3"):
            HourlyExposure(pm25_ug_m3=-1.0, stability="neutral")

    def test_validates_stability(self) -> None:
        with pytest.raises(ValueError, match="stability"):
            HourlyExposure(pm25_ug_m3=10.0, stability="bogus")


class TestPhenologyWeight:
    def test_dormant_no_weight(self) -> None:
        assert phenology_weight(BBCH.DORMANT) == 0.0

    def test_veraison_full_weight(self) -> None:
        assert phenology_weight(BBCH.VERAISON) == 1.0

    def test_flowering_partial(self) -> None:
        # Strictly between dormant and veraison.
        w = phenology_weight(BBCH.FLOWERING)
        assert 0.0 < w < 1.0


class TestSmokeDose:
    def test_empty_day(self) -> None:
        d = smoke_dose_index([], bbch=BBCH.VERAISON)
        assert d.dose == 0.0
        assert d.level == "low"
        assert d.hours_smoky == 0

    def test_clean_air_low_level(self) -> None:
        hours = [_hour(5.0)] * 24
        d = smoke_dose_index(hours, bbch=BBCH.VERAISON)
        assert d.level == "low"
        assert d.hours_smoky == 0
        assert d.pm25_max == 5.0

    def test_smoky_post_veraison_high_dose(self) -> None:
        # Sustained 100 µg/m³ for 12 h, stable BL → dose strongly elevated.
        hours = [_hour(100.0, "stable")] * 12 + [_hour(20.0)] * 12
        d = smoke_dose_index(hours, bbch=BBCH.VERAISON)
        # excess (100-35) * stable 1.5 * pheno 1.0 * 12 = 1170 — extreme.
        assert d.dose > LEVEL_HIGH_MAX
        assert d.level == "extreme"

    def test_pre_veraison_attenuated(self) -> None:
        hours = [_hour(100.0, "stable")] * 12
        post = smoke_dose_index(hours, bbch=BBCH.VERAISON).dose
        pre = smoke_dose_index(hours, bbch=BBCH.FLOWERING).dose
        assert pre < post

    def test_smoky_hour_count(self) -> None:
        hours = [_hour(50.0)] * 4 + [_hour(10.0)] * 20
        d = smoke_dose_index(hours, bbch=BBCH.VERAISON, pm25_smoky_threshold=35.0)
        assert d.hours_smoky == 4

    def test_dormant_block_zero_dose(self) -> None:
        hours = [_hour(200.0)] * 24
        d = smoke_dose_index(hours, bbch=BBCH.DORMANT)
        assert d.dose == 0.0
        assert d.level == "low"


def test_thresholds_ordered() -> None:
    assert LEVEL_LOW_MAX < LEVEL_ELEVATED_MAX < LEVEL_HIGH_MAX
