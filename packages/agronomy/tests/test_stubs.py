"""Public-surface smoke test.

Stage 00 stubbed every wedge with ``NotImplementedError``; Stage 01
implements them all. This file is now a thin smoke test that verifies
the public surface is callable end-to-end (catches accidental removal
of a re-export from ``agronomy.__init__`` or any wedge ``__init__``).

The detailed tests live in the per-wedge modules below.
"""

from __future__ import annotations

from agronomy import (
    BOTRYTIS_MODEL_VERSION,
    DM_MODEL_VERSION,
    FROST_MODEL_VERSION,
    PHENOLOGY_MODEL_VERSION,
    PM_MODEL_VERSION,
    SMOKE_MODEL_VERSION,
    disease,
    phenology,
    smoke,
)
from agronomy.thresholds import (
    BOTRYTIS_HIGH_PROB,
    DMCAST_HIGH_DSV_7D,
    FIRMS_RISK_RADIUS_KM,
    FROST_ALERT_TMIN_C,
    PM_HIGH_INDEX,
    SMOKE_HIGH_DOSE,
)


def test_thresholds_are_sane() -> None:
    """Sanity check on threshold constants — guards against accidental
    sign flips during refactors."""
    assert FROST_ALERT_TMIN_C < 0
    assert SMOKE_HIGH_DOSE > 0
    assert DMCAST_HIGH_DSV_7D > 0
    assert 0 < BOTRYTIS_HIGH_PROB < 1
    assert PM_HIGH_INDEX > 0
    assert FIRMS_RISK_RADIUS_KM > 0


def test_model_versions_are_set() -> None:
    """Every wedge version follows ``name@x.y.z``."""
    for v in (
        FROST_MODEL_VERSION,
        DM_MODEL_VERSION,
        PM_MODEL_VERSION,
        BOTRYTIS_MODEL_VERSION,
        SMOKE_MODEL_VERSION,
        PHENOLOGY_MODEL_VERSION,
    ):
        assert "@" in v
        name, version = v.split("@")
        assert name and version
        assert len(version.split(".")) == 3


def test_public_surface_callable() -> None:
    """Each wedge exports at least one callable matching the canonical
    function name. Catches refactors that orphan a public function."""
    assert callable(disease.dmcast_dsv)
    assert callable(disease.gubler_thomas_index)
    assert callable(disease.botrytis_infection_probability)
    assert callable(smoke.smoke_dose_index)
    assert callable(phenology.winkler_gdd)
    assert callable(phenology.caffarra_eccel_bbch)
    assert callable(phenology.fao56_eto)
    assert callable(phenology.swb_step)
