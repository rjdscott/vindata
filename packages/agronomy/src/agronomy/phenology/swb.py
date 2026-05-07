"""Single-bucket soil water balance (FAO-56 §7).

A daily lumped reservoir model: rainfall plus irrigation refill the bucket;
crop ET (Kc·ETo) and drainage deplete it. The bucket is bounded by the
total available water (TAW) of the rooting zone.

Reference:

    Allen, R.G. et al. (1998). "Crop evapotranspiration — guidelines for
    computing crop water requirements." FAO-56, §7. The Kc curve for grape
    is Kc_ini=0.30, Kc_mid=0.70, Kc_end=0.45 (FAO-56 Table 12, "grapes
    table grapes"). Wine grape Kc differs slightly per cultivar; this is
    a defensible default.

This module is intentionally simple: no canopy interception, no capillary
rise, no two-stage ET reduction. Stage 01 will swap in FAO-56 dual Kc on
calibrated AWRI vineyard plots.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from agronomy.phenology.caffarra_eccel import BBCH

#: Default Kc curve for grapes (FAO-56 Table 12, single Kc).
KC_INI: Final[float] = 0.30
KC_MID: Final[float] = 0.70
KC_END: Final[float] = 0.45


@dataclass(frozen=True, slots=True)
class BucketParams:
    """Soil reservoir parameters for one block.

    ``taw_mm`` is the total available water in the rooting depth, computed
    from soil texture (FAO-56 Table 19). Default 150 mm represents a
    moderate loam at 1 m rooting depth — typical for Orange basalt soils.

    ``maw_frac`` is the fraction of TAW that's readily available before
    stress sets in (the "p" coefficient in FAO-56). Default 0.45 is
    grape's tabulated value (FAO-56 Table 22).
    """

    taw_mm: float = 150.0
    maw_frac: float = 0.45


@dataclass(frozen=True, slots=True)
class BucketState:
    """Bucket level after one daily step."""

    sw_mm: float
    depletion_mm: float
    stress_fraction: float


def kc_for_stage(bbch: BBCH) -> float:
    """Single-Kc lookup keyed off the current BBCH stage.

    Mapping (consistent with FAO-56 four-stage curve):

      * Dormant / pre-budbreak → Kc_ini (no canopy)
      * Budbreak through flowering → linear interpolation from ini to mid
      * Flowering through veraison → Kc_mid (full canopy)
      * Veraison through maturity → linear interpolation from mid to end
      * Post-maturity → Kc_end
    """
    if bbch < BBCH.BUDBREAK:
        return KC_INI
    if bbch < BBCH.FLOWERING:
        # Approximate ini→mid ramp by midpoint.
        return (KC_INI + KC_MID) / 2.0
    if bbch < BBCH.VERAISON:
        return KC_MID
    if bbch < BBCH.MATURITY:
        return (KC_MID + KC_END) / 2.0
    return KC_END


def swb_step(
    sw_mm: float,
    *,
    eto_mm: float,
    rain_mm: float,
    irrigation_mm: float = 0.0,
    bbch: BBCH = BBCH.FLOWERING,
    params: BucketParams = BucketParams(),
) -> BucketState:
    """Advance the single-bucket SWB by one daily step.

    Args:
        sw_mm: Current soil-water content (mm in the bucket).
        eto_mm: Reference ETo for the day (mm/d, from ``fao56_eto``).
        rain_mm: Daily rainfall (mm).
        irrigation_mm: Daily irrigation (mm). Defaults to 0.
        bbch: Phenology stage that determines Kc.
        params: Bucket parameters.

    Returns:
        ``BucketState`` with the updated bucket level, the depletion
        relative to field capacity, and a stress fraction in [0, 1] where
        0 = no stress and 1 = full stress (depletion past MAW threshold).
    """
    if eto_mm < 0 or rain_mm < 0 or irrigation_mm < 0:
        raise ValueError("eto/rain/irrigation must be >= 0")
    if sw_mm < 0:
        raise ValueError("sw_mm must be >= 0")

    kc = kc_for_stage(bbch)
    etc = kc * eto_mm
    inflow = rain_mm + irrigation_mm

    # Apply inflows before ET (better proxy for the order-of-events on a
    # day with a rainfall pulse — water is available to the canopy).
    new_sw = sw_mm + inflow - etc

    # Bound by [0, TAW]; overflow is treated as drainage/runoff (we don't
    # surface that quantity since the wedge consumer doesn't need it yet).
    new_sw = max(0.0, min(params.taw_mm, new_sw))

    depletion = params.taw_mm - new_sw
    raw_threshold = params.maw_frac * params.taw_mm
    if depletion <= raw_threshold:
        stress = 0.0
    else:
        # Linear stress between MAW and TAW (full bucket empty).
        stress = min(1.0, (depletion - raw_threshold) / (params.taw_mm - raw_threshold))

    return BucketState(sw_mm=new_sw, depletion_mm=depletion, stress_fraction=stress)
