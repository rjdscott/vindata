"""Software-defined assets, grouped by stage of the pipeline.

   raw_open_meteo_forecast  ──▶  curated_forecast  ──▶  frost_score
"""

from vindata_ingest.assets.curated_forecast import curated_forecast
from vindata_ingest.assets.frost_score import frost_score
from vindata_ingest.assets.raw_open_meteo import (
    PILOT_VINEYARD_LOCATIONS,
    raw_open_meteo_forecast,
)

__all__ = [
    "PILOT_VINEYARD_LOCATIONS",
    "curated_forecast",
    "frost_score",
    "raw_open_meteo_forecast",
]
