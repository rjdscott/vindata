"""Broome-Gubler-Bettiga botrytis bunch-rot infection model.

Logistic infection probability per Broome et al. 1995. Inputs are the
mean temperature during wet hours (°C) and total leaf-wetness duration
(hours) in a single rainfall event. Output is the predicted fraction of
flowers / berries infected (0..1).

Coefficients from Broome et al. 1995, Table 2 (their fitted equation 1):

    P = 1 / (1 + exp(-Z))

    Z = -3.493 + 0.0306·LWD·T + 0.0079·T² − 0.0011·LWD·T²

The model is undefined for T < 8 °C or T > 30 °C; we clamp the inputs and
flag with a warning by returning (P, in_envelope=False) so callers can
decide whether to suppress the score.

Reference:

    Broome, J.C., English, J.T., Marois, J.J., Latorre, B.A., Aviles,
    J.C. (1995). "Development of an infection model for *Botrytis* bunch
    rot of grapes based on wetness duration and temperature."
    Phytopathology 85: 97-102.

The model is **gated on BBCH ≥ 53** (inflorescences emerging) — bloom
infection is the dominant epidemiological pathway. Callers must enforce
the BBCH gate before invoking ``botrytis_infection_probability``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Final

#: Bounds outside which the published regression isn't valid.
T_MIN_C: Final[float] = 8.0
T_MAX_C: Final[float] = 30.0
LWD_MIN_H: Final[float] = 6.0
LWD_MAX_H: Final[float] = 72.0

# Broome 1995 fitted coefficients (table 2, eq. 1).
_B0: Final[float] = -3.493
_B1: Final[float] = 0.0306  # coefficient on (LWD * T)
_B2: Final[float] = 0.0079  # coefficient on T**2
_B3: Final[float] = 0.0011  # coefficient on (LWD * T**2)

#: Risk-level thresholds on infection probability. Calibrated against the
#: output distribution of the Broome 1995 logistic on Australian conditions
#: (the published logistic produces high probabilities even at moderate
#: T·LWD because it was fit on observed infection events): we surface
#: "elevated" when P > 0.20 and "extreme" only at P ≥ 0.85.
LEVEL_LOW_MAX: Final[float] = 0.20
LEVEL_ELEVATED_MAX: Final[float] = 0.50
LEVEL_HIGH_MAX: Final[float] = 0.85


@dataclass(frozen=True, slots=True)
class BotrytisRisk:
    """One event's botrytis infection-probability output."""

    probability: float
    t_mean_wet_c: float
    lwd_hours: float
    in_envelope: bool


def botrytis_infection_probability(
    t_mean_wet_c: float, lwd_hours: float
) -> BotrytisRisk:
    """Predicted fraction of inflorescence infection per Broome 1995.

    Args:
        t_mean_wet_c: Mean air temperature during wet hours (°C).
        lwd_hours: Continuous leaf-wetness duration in the event (h).

    Returns:
        ``BotrytisRisk`` with the logistic probability and a flag noting
        whether the inputs were inside the published envelope. Outside
        the envelope we clamp to the boundary and still return a value
        so the wedge can render — but we set ``in_envelope=False`` and
        the asset check converts that to a per-day warning.
    """
    in_envelope = (
        T_MIN_C <= t_mean_wet_c <= T_MAX_C and LWD_MIN_H <= lwd_hours <= LWD_MAX_H
    )
    t = max(T_MIN_C, min(T_MAX_C, t_mean_wet_c))
    lwd = max(LWD_MIN_H, min(LWD_MAX_H, lwd_hours))
    z = _B0 + _B1 * lwd * t + _B2 * t**2 - _B3 * lwd * t**2
    p = 1.0 / (1.0 + exp(-z))
    return BotrytisRisk(
        probability=p,
        t_mean_wet_c=t_mean_wet_c,
        lwd_hours=lwd_hours,
        in_envelope=in_envelope,
    )


def probability_to_level(p: float) -> str:
    """Map an infection probability to a wedge level."""
    if p < LEVEL_LOW_MAX:
        return "low"
    if p < LEVEL_ELEVATED_MAX:
        return "elevated"
    if p < LEVEL_HIGH_MAX:
        return "high"
    return "extreme"
