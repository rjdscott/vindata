"""Smoke-taint exposure-dose model.

Volatile-phenol smoke compounds (guaiacol, 4-methylguaiacol, syringol,
cresols) accumulate in grape skins through cuticular sorption. Empirical
dose–response work post 2019–20 Australian fires shows that **exposure
intensity × duration × phenology stage** is the dominant predictor of
sensory taint risk; PM2.5 is the workable remote proxy in the absence of
direct phenol measurements.

We compute a per-vineyard *daily* exposure dose:

    dose_day = Σ_h (PM2.5_h · stability_weight(t) · phenology_weight(BBCH))

with caps that prevent unbounded growth on long-duration low-PM smoke.

Reference:

    Coulter, A.D. et al. (2022). "Vineyard exposure to smoke from the
    2019–20 Australian bushfires." AJGWR 28: 322–332. (PM2.5-hour binning)

    Krstic, M.P. et al. (2015). "Review of smoke taint in wine: smoke-
    derived volatile phenols and their glycosidic metabolites in grapes
    and vines …" AJGWR 21: 537-553.

Phenology gating: only veraison-onwards exposure (BBCH ≥ 81) carries
appreciable risk; pre-veraison berries shed bound phenols during
ripening. We expose this as a piecewise weighting rather than a hard
filter so the dashboard can still surface "elevated near-veraison" days.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from agronomy.phenology.caffarra_eccel import BBCH

#: Boundary-layer-stability weights applied per hour. Stable nights (low
#: mixing) concentrate ground-level smoke; unstable noon hours dilute it.
STABILITY_WEIGHTS: Final[dict[str, float]] = {
    "stable": 1.5,
    "neutral": 1.0,
    "unstable": 0.6,
}

#: Phenology weights — only veraison-onwards meaningfully accumulates
#: phenol-bound dose. Pre-flowering exposure is essentially benign.
_PHENO_WEIGHTS: Final[dict[BBCH, float]] = {
    BBCH.DORMANT: 0.0,
    BBCH.BUDBREAK: 0.05,
    BBCH.FLOWERING: 0.20,
    BBCH.VERAISON: 1.00,
    BBCH.MATURITY: 0.80,
}

#: Dose threshold bands (PM2.5 µg·h/m³) — Coulter 2022 Table 3 binning.
LEVEL_LOW_MAX: Final[float] = 50.0
LEVEL_ELEVATED_MAX: Final[float] = 150.0
LEVEL_HIGH_MAX: Final[float] = 500.0


@dataclass(frozen=True, slots=True)
class HourlyExposure:
    """One hour of smoke exposure data."""

    pm25_ug_m3: float
    stability: str  # "stable" | "neutral" | "unstable"

    def __post_init__(self) -> None:
        if self.pm25_ug_m3 < 0:
            raise ValueError(f"pm25_ug_m3 must be >= 0: {self.pm25_ug_m3}")
        if self.stability not in STABILITY_WEIGHTS:
            raise ValueError(
                f"stability must be one of {set(STABILITY_WEIGHTS)}: {self.stability}"
            )


@dataclass(frozen=True, slots=True)
class SmokeDose:
    """Daily smoke-taint dose summary."""

    dose: float
    pm25_mean: float
    pm25_max: float
    hours_smoky: int
    bbch: BBCH
    level: str


def phenology_weight(bbch: BBCH) -> float:
    """Lookup the smoke-sensitivity weight for a phenology stage.

    Stages between table entries inherit the *lower* (more sensitive)
    weight to be conservative — e.g., a block in BBCH 73 (post-flowering,
    pre-veraison) gets the BBCH.FLOWERING weight, not VERAISON.
    """
    keys = sorted(_PHENO_WEIGHTS.keys(), reverse=True)
    for k in keys:
        if bbch >= k:
            return _PHENO_WEIGHTS[k]
    return _PHENO_WEIGHTS[BBCH.DORMANT]


def smoke_dose_index(
    hours: list[HourlyExposure],
    bbch: BBCH = BBCH.VERAISON,
    pm25_smoky_threshold: float = 35.0,
) -> SmokeDose:
    """Aggregate hourly exposure into a daily dose with risk level.

    Args:
        hours: Ordered hourly exposure samples for the day.
        bbch: The block's current phenology stage. Used to weight the
            dose — pre-veraison exposure adds little to taint risk.
        pm25_smoky_threshold: PM2.5 (µg/m³) above which an hour counts as
            "smoky". Default 35 µg/m³ aligns with the AU air-quality
            "Poor" band.

    Returns:
        ``SmokeDose`` carrying the weighted dose, raw daily PM2.5
        statistics, smoky-hour count, and a discrete risk level.
    """
    if not hours:
        return SmokeDose(
            dose=0.0,
            pm25_mean=0.0,
            pm25_max=0.0,
            hours_smoky=0,
            bbch=bbch,
            level="low",
        )

    pheno_w = phenology_weight(bbch)

    # Dose integrates only the *excess* over the smoky threshold so that
    # rural-background PM2.5 (5-15 ug/m3 on clean days) doesn't accumulate
    # spurious dose. Coulter 2022 sec. 3.1 uses 35 ug/m3 ("Poor" AQ band)
    # as the floor below which exposure is treated as background.
    dose = sum(
        max(0.0, h.pm25_ug_m3 - pm25_smoky_threshold)
        * STABILITY_WEIGHTS[h.stability]
        * pheno_w
        for h in hours
    )
    pm25s = [h.pm25_ug_m3 for h in hours]
    smoky = sum(1 for p in pm25s if p >= pm25_smoky_threshold)

    return SmokeDose(
        dose=dose,
        pm25_mean=sum(pm25s) / len(pm25s),
        pm25_max=max(pm25s),
        hours_smoky=smoky,
        bbch=bbch,
        level=_dose_to_level(dose),
    )


def _dose_to_level(dose: float) -> str:
    if dose < LEVEL_LOW_MAX:
        return "low"
    if dose < LEVEL_ELEVATED_MAX:
        return "elevated"
    if dose < LEVEL_HIGH_MAX:
        return "high"
    return "extreme"
