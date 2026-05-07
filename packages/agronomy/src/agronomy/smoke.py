"""Smoke-taint exposure-dose proxy. Stubbed at Stage 00.

Stage 01 implements the Coulter et al. 2022 PM2.5-hour bin mapping with
boundary-layer-stability and phenology weighting.
"""

from __future__ import annotations


def smoke_dose_index(*_args: object, **_kwargs: object) -> float:
    """Compute the smoke-taint exposure dose index (Stage 01)."""
    raise NotImplementedError("Smoke dose: implemented in Stage 01")
