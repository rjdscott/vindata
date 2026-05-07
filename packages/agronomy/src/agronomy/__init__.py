"""Viticultural agronomy models for VinData.

Stage 00 implements the frost wedge only. See ``agronomy.frost``.

The remaining wedges are stubbed with explicit ``NotImplementedError`` so
the package shape is correct and downstream type-checking is honest.
"""

from agronomy.frost import (
    ForecastSample,
    FrostLevel,
    FrostParams,
    FrostScore,
    predict_tmin,
    score_frost,
)
from agronomy.version import MODEL_VERSION

__all__ = [
    "MODEL_VERSION",
    "ForecastSample",
    "FrostLevel",
    "FrostParams",
    "FrostScore",
    "predict_tmin",
    "score_frost",
]
