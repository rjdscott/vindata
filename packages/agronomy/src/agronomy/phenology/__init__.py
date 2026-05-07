"""Vine phenology models.

Public surface:

    DailyTemps · winkler_gdd · huglin_index_day · cumulative_winkler
    BBCH · CaffarraEccelParams · CHARDONNAY · SHIRAZ · PINOT_NOIR
    params_for · PhenologyState · PhenologyTrace · caffarra_eccel_bbch
    EtoInputs · fao56_eto
    BucketParams · BucketState · kc_for_stage · swb_step

References:

  - GDD: Hall, A. and Jones, G.V. (2010). AJGWR 16: 389-404.
  - BBCH stage prediction: Caffarra, A. and Eccel, E. (2010). IJB 54: 255-267.
  - Reference ET: Allen, R.G. et al. (1998). FAO-56.
  - SWB: Allen et al. 1998 §7 (single-Kc).
"""

from __future__ import annotations

from agronomy.phenology.caffarra_eccel import (
    BBCH,
    CHARDONNAY,
    CULTIVAR_PARAMS,
    PINOT_NOIR,
    SHIRAZ,
    CaffarraEccelParams,
    PhenologyState,
    PhenologyTrace,
    caffarra_eccel_bbch,
    params_for,
)
from agronomy.phenology.fao56_eto import EtoInputs, fao56_eto
from agronomy.phenology.gdd import (
    DailyTemps,
    cumulative_winkler,
    huglin_index_day,
    winkler_gdd,
)
from agronomy.phenology.swb import (
    KC_END,
    KC_INI,
    KC_MID,
    BucketParams,
    BucketState,
    kc_for_stage,
    swb_step,
)

__all__ = [
    "BBCH",
    "CHARDONNAY",
    "CULTIVAR_PARAMS",
    "KC_END",
    "KC_INI",
    "KC_MID",
    "PINOT_NOIR",
    "SHIRAZ",
    "BucketParams",
    "BucketState",
    "CaffarraEccelParams",
    "DailyTemps",
    "EtoInputs",
    "PhenologyState",
    "PhenologyTrace",
    "caffarra_eccel_bbch",
    "cumulative_winkler",
    "fao56_eto",
    "huglin_index_day",
    "kc_for_stage",
    "params_for",
    "swb_step",
    "winkler_gdd",
]
