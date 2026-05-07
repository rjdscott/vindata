"""Per-model version strings, recorded with every score row.

Bumped (SemVer) whenever a model's outputs change for the same inputs.
Used as the ``model_version`` column on ``agronomy_scores``.
"""

from typing import Final

FROST_MODEL_VERSION: Final[str] = "frost@0.1.0"
DM_MODEL_VERSION: Final[str] = "dmcast@0.1.0"
PM_MODEL_VERSION: Final[str] = "gubler_thomas@0.1.0"
BOTRYTIS_MODEL_VERSION: Final[str] = "broome_botrytis@0.1.0"
SMOKE_MODEL_VERSION: Final[str] = "smoke_dose@0.1.0"
PHENOLOGY_MODEL_VERSION: Final[str] = "caffarra_eccel@0.1.0"

# Convenience alias — kept for backward compat with Stage 00 frost callers.
MODEL_VERSION: Final[str] = FROST_MODEL_VERSION
