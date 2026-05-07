"""Caffarra-Eccel BBCH model tests.

Verifies stage transitions along a synthetic Orange-NSW season and the
cultivar-parameter resolution path.
"""

from __future__ import annotations

from itertools import pairwise

import pytest

from agronomy.phenology.caffarra_eccel import (
    BBCH,
    CHARDONNAY,
    SHIRAZ,
    CaffarraEccelParams,
    caffarra_eccel_bbch,
    params_for,
)
from agronomy.phenology.gdd import DailyTemps


def _winter_days(n: int, tmean: float = 4.0) -> list[DailyTemps]:
    """A run of cool days inside the chill window."""
    return [DailyTemps(tmin_c=tmean - 2, tmax_c=tmean + 2)] * n


def _spring_days(n: int, tmean: float = 14.0) -> list[DailyTemps]:
    """A run of warm-enough days that accumulate forcing."""
    return [DailyTemps(tmin_c=tmean - 4, tmax_c=tmean + 4)] * n


def _hot_summer_days(n: int, tmean: float = 22.0) -> list[DailyTemps]:
    """Hot days driving GDD-from-budbreak."""
    return [DailyTemps(tmin_c=tmean - 6, tmax_c=tmean + 6)] * n


class TestParamsFor:
    def test_default_is_chardonnay(self) -> None:
        assert params_for(None) is CHARDONNAY

    def test_known_cultivars(self) -> None:
        assert params_for("Shiraz") is SHIRAZ
        assert params_for("syrah") is SHIRAZ
        assert params_for("Pinot Noir").gdd_to_flowering == 320.0

    def test_unknown_falls_back(self) -> None:
        assert params_for("Made Up Grape") is CHARDONNAY


class TestCaffarraEccelTrace:
    def test_empty_input(self) -> None:
        trace = caffarra_eccel_bbch([], start_doy=1)
        assert trace.states == []
        assert trace.budbreak_doy is None

    def test_chill_only_no_budbreak(self) -> None:
        # 30 days of chill — won't reach C_crit = 60.
        days = _winter_days(30)
        trace = caffarra_eccel_bbch(days, start_doy=152)  # Jun 1 SH
        assert trace.budbreak_doy is None
        last = trace.states[-1]
        assert last.bbch is BBCH.DORMANT
        assert last.chill_units == pytest.approx(30.0)
        assert last.forcing_dd == 0.0

    def test_full_season_reaches_maturity(self) -> None:
        # Synthetic season: 90 cool, 60 mid, 60 hot, 60 hot.
        days = (
            _winter_days(90)
            + _spring_days(60, tmean=12.0)
            + _hot_summer_days(60, tmean=20.0)
            + _hot_summer_days(60, tmean=22.0)
        )
        trace = caffarra_eccel_bbch(days, start_doy=121)  # 1 May
        # Must hit at least flowering.
        assert trace.budbreak_doy is not None
        assert trace.flowering_doy is not None

    def test_shiraz_later_than_chardonnay(self) -> None:
        days = (
            _winter_days(120)
            + _spring_days(120, tmean=13.0)
        )
        ch = caffarra_eccel_bbch(days, start_doy=121, params=CHARDONNAY)
        sh = caffarra_eccel_bbch(days, start_doy=121, params=SHIRAZ)
        # Shiraz needs more forcing → budbreak strictly later or equal.
        assert ch.budbreak_doy is not None
        assert sh.budbreak_doy is not None
        assert sh.budbreak_doy >= ch.budbreak_doy

    def test_state_invariants(self) -> None:
        days = _winter_days(60) + _spring_days(60)
        trace = caffarra_eccel_bbch(days, start_doy=121)
        # Chill is monotone non-decreasing.
        chills = [s.chill_units for s in trace.states]
        assert all(b >= a for a, b in pairwise(chills))
        # Forcing is monotone non-decreasing.
        forces = [s.forcing_dd for s in trace.states]
        assert all(b >= a for a, b in pairwise(forces))


class TestCustomParams:
    def test_low_chill_crit_unblocks_quickly(self) -> None:
        # Replace chill_crit with 5 so a tiny chill bank releases dormancy.
        p = CaffarraEccelParams(chill_crit=5, force_crit=20)
        days = _winter_days(10) + _spring_days(20)
        trace = caffarra_eccel_bbch(days, start_doy=1, params=p)
        assert trace.budbreak_doy is not None
