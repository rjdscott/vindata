"""Single-bucket SWB tests."""

from __future__ import annotations

import pytest

from agronomy.phenology.caffarra_eccel import BBCH
from agronomy.phenology.swb import (
    KC_END,
    KC_INI,
    KC_MID,
    BucketParams,
    kc_for_stage,
    swb_step,
)


class TestKcLookup:
    def test_dormant_uses_initial(self) -> None:
        assert kc_for_stage(BBCH.DORMANT) == KC_INI

    def test_flowering_uses_mid(self) -> None:
        assert kc_for_stage(BBCH.FLOWERING) == KC_MID

    def test_maturity_uses_end(self) -> None:
        assert kc_for_stage(BBCH.MATURITY) == KC_END

    def test_budbreak_between_ini_and_mid(self) -> None:
        kc = kc_for_stage(BBCH.BUDBREAK)
        assert KC_INI < kc < KC_MID


class TestSwbStep:
    def test_dry_day_depletes(self) -> None:
        state = swb_step(
            sw_mm=100.0, eto_mm=5.0, rain_mm=0.0, bbch=BBCH.FLOWERING
        )
        # ETc = 0.7 * 5 = 3.5 → SW falls to 96.5
        assert state.sw_mm == pytest.approx(96.5)

    def test_rain_recharges_capped_at_taw(self) -> None:
        params = BucketParams(taw_mm=150.0)
        state = swb_step(
            sw_mm=140.0, eto_mm=2.0, rain_mm=50.0,
            bbch=BBCH.FLOWERING, params=params,
        )
        # rain (50) - ETc (1.4) > headroom; bucket caps at TAW.
        assert state.sw_mm == pytest.approx(150.0)
        assert state.depletion_mm == pytest.approx(0.0)
        assert state.stress_fraction == 0.0

    def test_severe_depletion_triggers_stress(self) -> None:
        params = BucketParams(taw_mm=100.0, maw_frac=0.4)
        # Bucket nearly empty.
        state = swb_step(
            sw_mm=10.0, eto_mm=8.0, rain_mm=0.0,
            bbch=BBCH.VERAISON, params=params,
        )
        assert state.sw_mm < 10.0
        # Depletion well past MAW threshold (40 mm) → strictly positive stress.
        assert state.stress_fraction > 0.0

    def test_irrigation_adds_to_inflow(self) -> None:
        a = swb_step(sw_mm=50.0, eto_mm=5.0, rain_mm=0.0, irrigation_mm=0.0)
        b = swb_step(sw_mm=50.0, eto_mm=5.0, rain_mm=0.0, irrigation_mm=20.0)
        assert b.sw_mm == pytest.approx(a.sw_mm + 20.0)

    def test_validates_negatives(self) -> None:
        with pytest.raises(ValueError):
            swb_step(sw_mm=-1.0, eto_mm=5.0, rain_mm=0.0)
        with pytest.raises(ValueError):
            swb_step(sw_mm=10.0, eto_mm=-1.0, rain_mm=0.0)
