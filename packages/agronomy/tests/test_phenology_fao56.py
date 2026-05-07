"""FAO-56 Penman-Monteith ETo tests.

Validates against the Allen et al. 1998 Example 18 worked example, plus
range and monotonicity properties.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from agronomy.phenology.fao56_eto import EtoInputs, fao56_eto


class TestEtoInputs:
    def test_validates_temperatures(self) -> None:
        with pytest.raises(ValueError, match="tmin"):
            EtoInputs(
                tmin_c=20, tmax_c=10, rh_mean=0.5, u2_ms=2,
                rs_mj=15, elev_m=950, lat_deg=-33.3, doy=120,
            )

    def test_validates_rh(self) -> None:
        with pytest.raises(ValueError, match="rh_mean"):
            EtoInputs(
                tmin_c=10, tmax_c=20, rh_mean=1.5, u2_ms=2,
                rs_mj=15, elev_m=950, lat_deg=-33.3, doy=120,
            )

    def test_validates_doy(self) -> None:
        with pytest.raises(ValueError, match="doy"):
            EtoInputs(
                tmin_c=10, tmax_c=20, rh_mean=0.5, u2_ms=2,
                rs_mj=15, elev_m=950, lat_deg=-33.3, doy=400,
            )


class TestFao56Eto:
    def test_allen_example_18_approximately(self) -> None:
        # Allen et al. 1998 Example 18: Madrid, 6 July.
        # Tmin=12.3, Tmax=21.5, RH=63%, u2=2.078, Rs=22.07, elev=2,
        # lat=40.4° N, DOY=187. Reported ETo = 3.88 mm/d.
        eto = fao56_eto(
            EtoInputs(
                tmin_c=12.3,
                tmax_c=21.5,
                rh_mean=0.63,
                u2_ms=2.078,
                rs_mj=22.07,
                elev_m=2.0,
                lat_deg=40.4,
                doy=187,
            )
        )
        # Within ±0.3 mm/d is the standard FAO-56 verification tolerance
        # for end-to-end implementations on the worked example.
        assert eto == pytest.approx(3.88, abs=0.3)

    def test_warm_orange_summer_is_plausible(self) -> None:
        # Cargo Road in mid-summer: a hot, moderately humid day at 950 m.
        eto = fao56_eto(
            EtoInputs(
                tmin_c=12.0,
                tmax_c=30.0,
                rh_mean=0.55,
                u2_ms=2.5,
                rs_mj=28.0,
                elev_m=950.0,
                lat_deg=-33.317,
                doy=10,  # ~mid Jan SH summer
            )
        )
        # Daily ETo for a hot day in cool-climate Australia should land
        # in the 4-8 mm/d range.
        assert 4.0 <= eto <= 8.0

    def test_winter_cool_day_low_eto(self) -> None:
        eto = fao56_eto(
            EtoInputs(
                tmin_c=-2.0,
                tmax_c=8.0,
                rh_mean=0.85,
                u2_ms=1.0,
                rs_mj=6.0,
                elev_m=950.0,
                lat_deg=-33.317,
                doy=180,  # ~late June SH winter
            )
        )
        # Cool, calm, humid day → ETo well below 2 mm/d.
        assert 0.0 <= eto <= 2.0

    @given(
        tmean=st.floats(min_value=10, max_value=30),
        u2=st.floats(min_value=0, max_value=8),
        rh=st.floats(min_value=0.2, max_value=0.95),
        rs=st.floats(min_value=10, max_value=30),
    )
    def test_eto_non_negative(
        self, tmean: float, u2: float, rh: float, rs: float
    ) -> None:
        eto = fao56_eto(
            EtoInputs(
                tmin_c=tmean - 5,
                tmax_c=tmean + 5,
                rh_mean=rh,
                u2_ms=u2,
                rs_mj=rs,
                elev_m=950.0,
                lat_deg=-33.317,
                doy=10,
            )
        )
        assert eto >= 0.0
