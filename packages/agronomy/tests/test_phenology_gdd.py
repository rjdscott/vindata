"""Winkler / Huglin GDD tests.

Verifies the equation against worked examples and uses Hypothesis to
prove monotonicity properties (warmer day → ≥ GDD).
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from agronomy.phenology.gdd import (
    DailyTemps,
    cumulative_winkler,
    huglin_index_day,
    winkler_gdd,
)


class TestDailyTemps:
    def test_construct_valid(self) -> None:
        d = DailyTemps(tmin_c=5.0, tmax_c=20.0)
        assert d.tmean_c == pytest.approx(12.5)

    def test_rejects_inverted(self) -> None:
        with pytest.raises(ValueError, match="tmax_c"):
            DailyTemps(tmin_c=20.0, tmax_c=5.0)

    def test_rejects_extreme(self) -> None:
        with pytest.raises(ValueError, match="tmin_c"):
            DailyTemps(tmin_c=-100.0, tmax_c=10.0)


class TestWinklerGDD:
    def test_zero_when_below_base(self) -> None:
        d = DailyTemps(tmin_c=2.0, tmax_c=8.0)  # mean = 5 < base 10
        assert winkler_gdd(d) == 0.0

    def test_known_example(self) -> None:
        # Mean = 17.5 °C → GDD = 7.5 °C·d
        d = DailyTemps(tmin_c=10.0, tmax_c=25.0)
        assert winkler_gdd(d) == pytest.approx(7.5)

    def test_custom_base(self) -> None:
        d = DailyTemps(tmin_c=10.0, tmax_c=20.0)  # mean = 15
        assert winkler_gdd(d, base_c=12.0) == pytest.approx(3.0)

    @given(
        tmin=st.floats(min_value=-30, max_value=30),
        delta=st.floats(min_value=0.1, max_value=20),
    )
    def test_monotone_in_temperature(self, tmin: float, delta: float) -> None:
        cool = DailyTemps(tmin_c=tmin, tmax_c=tmin + delta)
        warm = DailyTemps(tmin_c=tmin + 1, tmax_c=tmin + 1 + delta)
        assert winkler_gdd(warm) >= winkler_gdd(cool)


class TestHuglinIndex:
    def test_zero_below_base(self) -> None:
        d = DailyTemps(tmin_c=2.0, tmax_c=8.0)
        assert huglin_index_day(d, latitude_deg=-33.317) == 0.0

    def test_uses_latitude_k(self) -> None:
        # At higher latitude K is larger, so the index for the same day
        # should be at least as large.
        d = DailyTemps(tmin_c=15.0, tmax_c=30.0)
        low = huglin_index_day(d, latitude_deg=30.0)
        high = huglin_index_day(d, latitude_deg=48.0)
        assert high > low

    def test_southern_hemisphere_symmetry(self) -> None:
        d = DailyTemps(tmin_c=15.0, tmax_c=30.0)
        north = huglin_index_day(d, latitude_deg=44.0)
        south = huglin_index_day(d, latitude_deg=-44.0)
        assert north == pytest.approx(south)


class TestCumulative:
    def test_empty_list(self) -> None:
        assert cumulative_winkler([]) == 0.0

    def test_seven_days_growing_season(self) -> None:
        days = [DailyTemps(tmin_c=10, tmax_c=25)] * 7  # 7.5 GDD/day
        assert cumulative_winkler(days) == pytest.approx(52.5)
