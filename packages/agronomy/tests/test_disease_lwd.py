"""NEWA CART leaf-wetness proxy tests."""

from __future__ import annotations

import pytest

from agronomy.disease.lwd import (
    HourlyWeather,
    hourly_lwd,
    is_wet_hour,
    mean_temp_during_wet,
)


def _hour(t: float = 15.0, td: float = 10.0, rh: float = 60.0, p: float = 0.0) -> HourlyWeather:
    return HourlyWeather(t2m_c=t, dewpoint_c=td, rh_pct=rh, precip_mm=p)


class TestHourlyWeather:
    def test_validates_rh(self) -> None:
        with pytest.raises(ValueError, match="rh_pct"):
            HourlyWeather(t2m_c=15, dewpoint_c=10, rh_pct=120, precip_mm=0)

    def test_validates_dewpoint(self) -> None:
        with pytest.raises(ValueError, match="dewpoint"):
            HourlyWeather(t2m_c=10, dewpoint_c=15, rh_pct=80, precip_mm=0)


class TestIsWetHour:
    def test_high_rh_is_wet(self) -> None:
        assert is_wet_hour(_hour(rh=92.0))

    def test_precip_is_wet(self) -> None:
        assert is_wet_hour(_hour(rh=70.0, p=0.5))

    def test_dewpoint_close_is_wet(self) -> None:
        # Dewpoint depression = 1.0 °C → wet via the third clause.
        assert is_wet_hour(_hour(t=10.0, td=9.0, rh=80.0))

    def test_dry_warm_day(self) -> None:
        assert not is_wet_hour(_hour(t=25.0, td=10.0, rh=40.0))


class TestHourlyLwd:
    def test_empty(self) -> None:
        assert hourly_lwd([]) == 0
        assert mean_temp_during_wet([]) is None

    def test_count_and_temperature(self) -> None:
        wet = [_hour(t=12.0, rh=92.0)] * 4
        dry = [_hour(t=25.0, rh=40.0)] * 6
        hours = wet + dry
        assert hourly_lwd(hours) == 4
        assert mean_temp_during_wet(hours) == pytest.approx(12.0)
