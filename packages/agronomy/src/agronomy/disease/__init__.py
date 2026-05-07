"""Vine disease pressure models.

Public surface:

    HourlyWeather · is_wet_hour · hourly_lwd · mean_temp_during_wet
    DmcastDay · dmcast_dsv
    GublerThomasDay · gubler_thomas_index · index_to_level
    BotrytisRisk · botrytis_infection_probability · probability_to_level

References (canonical):

  - Magarey-Wachtel 2002 (DMCast / downy)
  - Gubler-Thomas 1999 (UC IPM Risk Index / powdery)
  - Broome-Gubler-Bettiga 1995 (botrytis bunch rot)
  - Gleason et al. 1994 (NEWA CART leaf-wetness rule)
"""

from __future__ import annotations

from agronomy.disease.broome_botrytis import (
    BotrytisRisk,
    botrytis_infection_probability,
    probability_to_level,
)
from agronomy.disease.dmcast import DmcastDay, dmcast_dsv
from agronomy.disease.gubler_thomas import (
    GublerThomasDay,
    gubler_thomas_index,
    index_to_level,
)
from agronomy.disease.lwd import (
    HourlyWeather,
    hourly_lwd,
    is_wet_hour,
    mean_temp_during_wet,
)

__all__ = [
    "BotrytisRisk",
    "DmcastDay",
    "GublerThomasDay",
    "HourlyWeather",
    "botrytis_infection_probability",
    "dmcast_dsv",
    "gubler_thomas_index",
    "hourly_lwd",
    "index_to_level",
    "is_wet_hour",
    "mean_temp_during_wet",
    "probability_to_level",
]
