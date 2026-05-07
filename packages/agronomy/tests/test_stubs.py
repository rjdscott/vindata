"""Stage 00 stub contract: every unimplemented wedge must raise
``NotImplementedError`` when called, so callers can never silently treat a
zero return as a valid score.
"""

from __future__ import annotations

import pytest

from agronomy.disease.broome_botrytis import botrytis_infection_probability
from agronomy.disease.dmcast import dmcast_dsv
from agronomy.disease.gubler_thomas import gubler_thomas_index
from agronomy.phenology.caffarra_eccel import caffarra_eccel_bbch
from agronomy.phenology.fao56_eto import fao56_eto
from agronomy.phenology.gdd import winkler_gdd
from agronomy.phenology.swb import swb_step
from agronomy.smoke import smoke_dose_index
from agronomy.thresholds import FROST_ALERT_TMIN_C, SMOKE_HIGH_DOSE


@pytest.mark.parametrize(
    "func",
    [
        dmcast_dsv,
        gubler_thomas_index,
        botrytis_infection_probability,
        smoke_dose_index,
        winkler_gdd,
        caffarra_eccel_bbch,
        fao56_eto,
        swb_step,
    ],
)
def test_stubs_raise(func: object) -> None:
    with pytest.raises(NotImplementedError):
        func()  # type: ignore[operator]


def test_thresholds_are_sane() -> None:
    """Sanity check on threshold constants — guards against accidental
    sign flips during refactors."""
    assert FROST_ALERT_TMIN_C < 0
    assert SMOKE_HIGH_DOSE > 0
