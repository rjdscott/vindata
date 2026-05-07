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
#: Mirrors ``agronomy.smoke.LEVEL_HIGH_MAX`` and is re-exposed here so the
#: API can render banners without importing the model module.
SMOKE_HIGH_DOSE: Final[float] = 500.0

#: Disease: cumulative DSV within a 7-day window that constitutes a
#: "high" downy-mildew advisory. Mirrors ``agronomy.disease.dmcast``.
DMCAST_HIGH_DSV_7D: Final[int] = 6

#: Disease: Gubler-Thomas index above which the powdery-mildew advisory
#: shows "high" in the dashboard.
PM_HIGH_INDEX: Final[int] = 60

#: Disease: Broome-Bettiga botrytis predicted infection probability above
#: which the botrytis advisory shows "high". See ``broome_botrytis.py`` for
#: the calibration rationale (logistic was fit on observed infection events,
#: so absolute probabilities run higher than naive intuition suggests).
BOTRYTIS_HIGH_PROB: Final[float] = 0.50

#: FIRMS hotspot proximity (km) within which a hotspot is considered a
#: smoke-taint risk vector. Coulter 2022 used 100 km.
FIRMS_RISK_RADIUS_KM: Final[float] = 100.0
