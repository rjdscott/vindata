"""Viticultural agronomy models for VinData.

Implements four wedges:

  * **Frost** (``agronomy.frost``) — Snyder & de Melo-Abreu radiation
    cooling Tmin predictor with block-scale cold-air drainage.
  * **Disease** (``agronomy.disease``) — DMCast (downy), Gubler-Thomas
    (powdery), Broome-Bettiga (botrytis), plus the NEWA CART leaf-wetness
    proxy.
  * **Smoke-taint** (``agronomy.smoke``) — Coulter 2022-style PM2.5 dose
    weighted by boundary-layer stability and phenology stage.
  * **Phenology** (``agronomy.phenology``) — Winkler GDD, Caffarra-Eccel
    chilling+forcing BBCH, FAO-56 ETo, single-bucket SWB.

All four are pure-Python, no globals, fully typed, ≥ 85% test coverage,
zero I/O. They are designed to be called from a Dagster scoring asset
or a Lambda; they make no assumption about how their inputs are sourced.
"""

from agronomy import disease, phenology, smoke
from agronomy.frost import (
    ForecastSample,
    FrostLevel,
    FrostParams,
    FrostScore,
    predict_tmin,
    score_frost,
)
from agronomy.version import (
    BOTRYTIS_MODEL_VERSION,
    DM_MODEL_VERSION,
    FROST_MODEL_VERSION,
    MODEL_VERSION,
    PHENOLOGY_MODEL_VERSION,
    PM_MODEL_VERSION,
    SMOKE_MODEL_VERSION,
)

__all__ = [
    "BOTRYTIS_MODEL_VERSION",
    "DM_MODEL_VERSION",
    "FROST_MODEL_VERSION",
    "MODEL_VERSION",
    "PHENOLOGY_MODEL_VERSION",
    "PM_MODEL_VERSION",
    "SMOKE_MODEL_VERSION",
    "ForecastSample",
    "FrostLevel",
    "FrostParams",
    "FrostScore",
    "disease",
    "phenology",
    "predict_tmin",
    "score_frost",
    "smoke",
]
