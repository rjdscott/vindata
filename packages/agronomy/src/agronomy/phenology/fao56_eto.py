"""FAO-56 Penman-Monteith reference evapotranspiration (daily).

Implements equation 6 of Allen et al. (1998) for daily reference ETo, using
the standard simplifications when only Tmin/Tmax/RHmean/u2/Rs/elevation/lat
are available. All units SI.

Reference:

    Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). "Crop
    evapotranspiration — guidelines for computing crop water requirements."
    FAO Irrigation and Drainage Paper 56. Rome: FAO.

This module is pure; no globals; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, cos, exp, pi, sin, sqrt, tan

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

#: Solar constant (MJ m^-2 min^-1), Allen et al. eq. 28.
GSC: float = 0.0820
#: Stefan-Boltzmann constant (MJ K^-4 m^-2 d^-1), Allen et al. eq. 39.
SIGMA: float = 4.903e-9
#: Albedo for the reference grass surface (Allen et al. eq. 38).
ALBEDO_REF: float = 0.23


@dataclass(frozen=True, slots=True)
class EtoInputs:
    """One day's inputs for the FAO-56 ETo calculation.

    All fields use the standard FAO-56 conventions:

    * ``tmin_c, tmax_c``: 2 m air temperature daily extrema (°C).
    * ``rh_mean``: daily mean RH as a fraction in [0, 1].
    * ``u2_ms``: 2-m wind speed (m/s). If only u10 is available, scale by
      ``4.87 / ln(67.8·10 - 5.42)`` per Allen eq. 47 — caller's job.
    * ``rs_mj``: incoming solar radiation (MJ m^-2 d^-1). If only sunshine
      hours, convert via Angstrom upstream.
    * ``elev_m``: site elevation (m above sea level).
    * ``lat_deg``: latitude in degrees, signed (SH negative).
    * ``doy``: day of year (1..366).
    """

    tmin_c: float
    tmax_c: float
    rh_mean: float
    u2_ms: float
    rs_mj: float
    elev_m: float
    lat_deg: float
    doy: int

    def __post_init__(self) -> None:
        if not self.tmin_c <= self.tmax_c:
            raise ValueError(f"tmin {self.tmin_c} must be <= tmax {self.tmax_c}")
        if not 0.0 <= self.rh_mean <= 1.0:
            raise ValueError(f"rh_mean must be in [0,1]: {self.rh_mean}")
        if self.u2_ms < 0:
            raise ValueError(f"u2_ms must be >= 0: {self.u2_ms}")
        if self.rs_mj < 0:
            raise ValueError(f"rs_mj must be >= 0: {self.rs_mj}")
        if not 1 <= self.doy <= 366:
            raise ValueError(f"doy must be in [1,366]: {self.doy}")


def _saturation_vapor_pressure(t_c: float) -> float:
    """Saturation vapour pressure at temperature t_c (kPa). Allen eq. 11."""
    return 0.6108 * exp(17.27 * t_c / (t_c + 237.3))


def _slope_svp(t_c: float) -> float:
    """Slope of the saturation vapour-pressure curve at t (kPa/°C). Eq. 13."""
    return (4098.0 * _saturation_vapor_pressure(t_c)) / ((t_c + 237.3) ** 2)


def _atmospheric_pressure(elev_m: float) -> float:
    """Atmospheric pressure (kPa) from elevation. Eq. 7."""
    return float(101.3 * ((293.0 - 0.0065 * elev_m) / 293.0) ** 5.26)


def _psychrometric_constant(p_kpa: float) -> float:
    """Psychrometric constant (kPa/°C) at pressure p_kpa. Eq. 8."""
    return 0.665e-3 * p_kpa


def _ra(lat_deg: float, doy: int) -> float:
    """Extraterrestrial radiation (MJ m^-2 d^-1). Allen eqs. 21–24."""
    phi = lat_deg * pi / 180.0
    dr = 1.0 + 0.033 * cos(2.0 * pi * doy / 365.0)
    delta = 0.409 * sin(2.0 * pi * doy / 365.0 - 1.39)
    # Sunset hour angle, eq. 25 — clamped to keep arccos arg in [-1, 1] at
    # high latitudes / midnight sun seasons (irrelevant in Orange but the
    # function should be globally robust).
    arg = -tan(phi) * tan(delta)
    arg = max(-1.0, min(1.0, arg))
    omega_s = _safe_acos(arg)
    return (
        (24.0 * 60.0 / pi)
        * GSC
        * dr
        * (omega_s * sin(phi) * sin(delta) + cos(phi) * cos(delta) * sin(omega_s))
    )


def _safe_acos(x: float) -> float:
    """Numerically robust acos: clamps to [-1, 1] before delegating."""
    return acos(max(-1.0, min(1.0, x)))


def fao56_eto(inputs: EtoInputs) -> float:
    """Daily reference ETo (mm/day) per Allen et al. 1998 eq. 6.

    Uses the standard simplifying assumption ``G ≈ 0`` for the daily
    timestep (soil heat flux is negligible over 24 h on a grass-covered
    surface — Allen et al. eq. 42).

    Returns mm/day. Never negative; clamps to zero on numerical edge
    cases (e.g., extreme cold combined with tiny radiation).
    """
    tmean = (inputs.tmin_c + inputs.tmax_c) / 2.0
    delta = _slope_svp(tmean)
    p = _atmospheric_pressure(inputs.elev_m)
    gamma = _psychrometric_constant(p)

    # Saturation vapour pressure: average of values at Tmin and Tmax
    # (Allen eq. 12).
    es_max = _saturation_vapor_pressure(inputs.tmax_c)
    es_min = _saturation_vapor_pressure(inputs.tmin_c)
    es = (es_max + es_min) / 2.0
    ea = inputs.rh_mean * es

    # Net shortwave radiation, eq. 38.
    rns = (1.0 - ALBEDO_REF) * inputs.rs_mj

    # Net longwave radiation, eq. 39.
    ra = _ra(inputs.lat_deg, inputs.doy)
    # Clear-sky radiation, eq. 37 (simplified to Rso = (0.75 + 2e-5·z)·Ra).
    rso = (0.75 + 2e-5 * inputs.elev_m) * ra
    rs_over_rso = inputs.rs_mj / rso if rso > 0 else 0.0
    rs_over_rso = max(0.0, min(1.0, rs_over_rso))

    tmax_k4 = (inputs.tmax_c + 273.16) ** 4
    tmin_k4 = (inputs.tmin_c + 273.16) ** 4
    rnl = SIGMA * ((tmax_k4 + tmin_k4) / 2.0) * (0.34 - 0.14 * sqrt(ea)) * (
        1.35 * rs_over_rso - 0.35
    )

    rn = rns - rnl  # MJ m^-2 d^-1
    # Daily soil heat flux (Allen eq. 42).
    g = 0.0

    numerator = (
        0.408 * delta * (rn - g)
        + gamma * (900.0 / (tmean + 273.0)) * inputs.u2_ms * (es - ea)
    )
    denominator = delta + gamma * (1.0 + 0.34 * inputs.u2_ms)
    eto = numerator / denominator
    return max(0.0, eto)
