"""Centralised thresholds used across wedges. Pure constants.

Kept in one place so calibration changes are auditable and don't drift
across the API and the scoring path.
"""

from __future__ import annotations

from typing import Final

#: Frost: predicted Tmin (°C) at or below which we trigger an alert
#: (Stage 01 sends an SES email; Stage 00 just renders a chip).
FROST_ALERT_TMIN_C: Final[float] = -1.0

#: Smoke: PM2.5 dose (µg·h/m³) post-veraison threshold for a "high" level.
SMOKE_HIGH_DOSE: Final[float] = 250.0
