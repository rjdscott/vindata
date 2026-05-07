"""Software-defined assets, grouped by stage of the pipeline.

   raw_open_meteo_forecast ─┐
                            ├──▶ curated_forecast ──▶ phenology_state ─┐
   raw_air_quality   ───────┤                                          ├──▶ disease_score
                            │                                          │
   raw_firms         ───────┘                                          └──▶ smoke_score
                                                          frost_score ──┘
"""

from vindata_ingest.assets.curated_forecast import curated_forecast
from vindata_ingest.assets.disease_score import disease_score
from vindata_ingest.assets.frost_score import frost_score
from vindata_ingest.assets.phenology_state import phenology_state
from vindata_ingest.assets.raw_air_quality import raw_air_quality
from vindata_ingest.assets.raw_firms import raw_firms
from vindata_ingest.assets.raw_open_meteo import (
    PILOT_VINEYARD_LOCATIONS,
    raw_open_meteo_forecast,
)
from vindata_ingest.assets.smoke_score import smoke_score

__all__ = [
    "PILOT_VINEYARD_LOCATIONS",
    "curated_forecast",
    "disease_score",
    "frost_score",
    "phenology_state",
    "raw_air_quality",
    "raw_firms",
    "raw_open_meteo_forecast",
    "smoke_score",
]
