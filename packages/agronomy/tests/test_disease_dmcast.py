"""DMCast (downy mildew) DSV tests.

Verifies the published Magarey-Wachtel table against the canonical
worked example: 18 °C wet hours produce DSV 3 at LWD 16, DSV 4 at 19.
"""

from __future__ import annotations

import pytest

from agronomy.disease.dmcast import dmcast_dsv
from agronomy.disease.lwd import HourlyWeather


def _wet_hour(t: float) -> HourlyWeather:
    """A wet hour at the given temperature (RH = 95%)."""
    return HourlyWeather(t2m_c=t, dewpoint_c=t - 1, rh_pct=95.0, precip_mm=0.0)


def _dry_hour(t: float) -> HourlyWeather:
    return HourlyWeather(t2m_c=t, dewpoint_c=t - 10, rh_pct=50.0, precip_mm=0.0)


class TestDmcastDsv:
    def test_dry_day_is_zero(self) -> None:
        result = dmcast_dsv([_dry_hour(20.0)] * 24)
        assert result.dsv == 0
        assert result.lwd_hours == 0

    def test_warm_band_threshold_three(self) -> None:
        # 15 wet hours at ~20 deg C -> DSV 3 in the 18-22 band (table says
        # 14h crosses to DSV 3; 16h crosses to DSV 4).
        hours = [_wet_hour(20.0)] * 15
        result = dmcast_dsv(hours)
        assert result.dsv == 3
        assert result.lwd_hours == 15
        assert result.t_mean_wet_c == pytest.approx(20.0)

    def test_warm_band_threshold_four(self) -> None:
        hours = [_wet_hour(20.0)] * 19
        result = dmcast_dsv(hours)
        assert result.dsv == 4

    def test_cool_band_needs_more_lwd(self) -> None:
        # 13 wet hours at ~12 deg C -> DSV 1 in the 10-14 band.
        hours = [_wet_hour(12.0)] * 13
        assert dmcast_dsv(hours).dsv == 1

    def test_outside_envelope_is_zero(self) -> None:
        # 8 °C wet — below the cool-band floor (10 °C).
        hours = [_wet_hour(8.0)] * 24
        assert dmcast_dsv(hours).dsv == 0
        # 32 °C wet — above the warm-band ceiling (30 °C).
        hours = [_wet_hour(32.0)] * 24
        assert dmcast_dsv(hours).dsv == 0
