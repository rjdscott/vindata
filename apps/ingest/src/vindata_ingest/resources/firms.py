"""NASA FIRMS active-fire client.

FIRMS (Fire Information for Resource Management System) is NASA's near-
real-time hotspot product, available via CSV at:

    https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{source}/{west,south,east,north}/{day_range}

A free MAP_KEY can be requested from the FIRMS website. Without one, the
resource still runs but in offline mode (empty results) so the rest of
the pipeline stays green — the smoke wedge will simply have no hotspot
context.

Reference: https://firms.modaps.eosdis.nasa.gov/api/area/

We default to MODIS_NRT (1 km resolution; updated ~3 h after observation)
because it's the broadest swath; VIIRS_SNPP_NRT is higher-resolution but
only covers two passes per day.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from dagster import ConfigurableResource
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """West, south, east, north — the order FIRMS expects."""

    west: float
    south: float
    east: float
    north: float

    def as_path(self) -> str:
        return f"{self.west},{self.south},{self.east},{self.north}"


#: Default 250 km bounding box around Mount Canobolas. Smoke from fires
#: outside this box can still reach the vineyards (see Coulter 2022 §3.2);
#: we widen via the resource config when calibrating the smoke wedge.
ORANGE_REGION_BBOX: BoundingBox = BoundingBox(
    west=146.5, south=-35.5, east=151.5, north=-31.5
)


class FirmsError(RuntimeError):
    """Raised on non-retriable API responses."""


class FirmsResource(ConfigurableResource):
    """FIRMS CSV client.

    Configuration:
      * ``base_url``: defaults to the public FIRMS area endpoint.
      * ``map_key``: free key from the FIRMS website. If empty, the
        resource is offline by default.
      * ``source``: ``MODIS_NRT`` | ``VIIRS_SNPP_NRT`` | ``VIIRS_NOAA20_NRT``.
      * ``timeout_s``: request timeout (seconds).
      * ``offline``: force offline mode regardless of map_key.
    """

    base_url: str = "https://firms.modaps.eosdis.nasa.gov"
    map_key: str = ""
    source: str = "MODIS_NRT"
    timeout_s: float = 30.0
    offline: bool = False

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _get_csv(self, path: str) -> str:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get(url)
            if 400 <= response.status_code < 500 and response.status_code != 429:
                raise FirmsError(
                    f"FIRMS {response.status_code}: {response.text[:200]}"
                )
            response.raise_for_status()
            return response.text

    def recent_hotspots(
        self,
        *,
        bbox: BoundingBox = ORANGE_REGION_BBOX,
        day_range: int = 1,
    ) -> list[dict[str, Any]]:
        """Pull recent active-fire hotspots in ``bbox`` for the last
        ``day_range`` days (1..10).

        Returns one dict per detection with normalised keys; an empty list
        when the API key is missing, the response is empty, or the network
        is unreachable.
        """
        if self.offline or not self.map_key:
            return []

        path = f"api/area/csv/{self.map_key}/{self.source}/{bbox.as_path()}/{day_range}"
        try:
            csv_text = self._get_csv(path)
        except (httpx.HTTPError, FirmsError):
            return []

        return _parse_firms_csv(csv_text, satellite=self.source)


def _parse_firms_csv(csv_text: str, *, satellite: str) -> list[dict[str, Any]]:
    """Parse a FIRMS CSV response into normalised dicts.

    The CSV header is documented at the FIRMS API page; we extract the
    fields ``fire_hotspots`` cares about and ignore the rest.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    out: list[dict[str, Any]] = []
    for row in reader:
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            acq_date = row["acq_date"]  # YYYY-MM-DD
            acq_time = row["acq_time"]  # HHMM
            ts = datetime.strptime(
                f"{acq_date} {acq_time.zfill(4)}", "%Y-%m-%d %H%M"
            )
        except (KeyError, ValueError):
            continue
        try:
            brightness = float(row.get("brightness", "")) if row.get("brightness") else None
            frp = float(row.get("frp", "")) if row.get("frp") else None
            confidence_raw = row.get("confidence", "")
            confidence = (
                int(float(confidence_raw))
                if confidence_raw and confidence_raw not in ("nominal", "low", "high")
                else None
            )
        except ValueError:
            brightness = None
            frp = None
            confidence = None
        out.append(
            {
                "ts": ts,
                "lat": lat,
                "lon": lon,
                "brightness_k": brightness,
                "frp_mw": frp,
                "satellite": satellite,
                "confidence": confidence,
            }
        )
    return out
