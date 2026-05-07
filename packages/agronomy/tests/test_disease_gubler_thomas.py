"""Gubler-Thomas powdery-mildew Risk Index tests.

Verifies the +20/block reward, -10 penalty, lethal-temperature drop, and
the [0, 100] clamp.
"""

from __future__ import annotations

from agronomy.disease.gubler_thomas import (
    INDEX_MAX,
    INDEX_MIN,
    LETHAL_T,
    OPTIMUM_T_HI,
    OPTIMUM_T_LO,
    gubler_thomas_index,
    index_to_level,
)
from agronomy.disease.lwd import HourlyWeather


def _hours(t_pattern: list[float]) -> list[HourlyWeather]:
    return [
        HourlyWeather(t2m_c=t, dewpoint_c=t - 5, rh_pct=60.0, precip_mm=0.0)
        for t in t_pattern
    ]


class TestGublerThomasStep:
    def test_three_optimum_blocks_max_reward(self) -> None:
        # 24 h all in optimum band -> 4 x 6-h blocks -> reward capped at +60.
        hours = _hours([25.0] * 24)
        day = gubler_thomas_index(hours, prior_index=0)
        assert day.optimum_blocks == 4
        assert day.delta == 60  # capped
        assert day.new_index == 60

    def test_full_optimum_reaches_max(self) -> None:
        # Several optimum days in a row should saturate at 100.
        idx = 0
        for _ in range(5):
            day = gubler_thomas_index(_hours([25.0] * 24), prior_index=idx)
            idx = day.new_index
        assert idx == INDEX_MAX

    def test_lethal_day_penalises(self) -> None:
        # One hour > 35 °C → -10 penalty regardless of optimum blocks.
        pattern = [25.0] * 12 + [LETHAL_T + 1] + [25.0] * 11
        day = gubler_thomas_index(_hours(pattern), prior_index=80)
        assert day.had_lethal
        assert day.new_index == 70

    def test_no_optimum_no_lethal_still_penalises(self) -> None:
        # Cool day, no optimum blocks → -10.
        day = gubler_thomas_index(_hours([15.0] * 24), prior_index=50)
        assert day.optimum_blocks == 0
        assert day.delta == -10
        assert day.new_index == 40

    def test_index_does_not_go_negative(self) -> None:
        day = gubler_thomas_index(_hours([15.0] * 24), prior_index=5)
        assert day.new_index == INDEX_MIN

    def test_optimum_band_constants_consistent(self) -> None:
        assert OPTIMUM_T_LO < OPTIMUM_T_HI < LETHAL_T


class TestLevelMapping:
    def test_thresholds(self) -> None:
        assert index_to_level(0) == "low"
        assert index_to_level(29) == "low"
        assert index_to_level(30) == "elevated"
        assert index_to_level(60) == "high"
        assert index_to_level(80) == "extreme"
