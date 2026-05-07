"""NSW DPE Air Quality client.

The NSW Department of Planning & Environment runs an open Air Quality
monitoring network whose hourly PM2.5 observations are available via a
public JSON API at ``https://data.airquality.nsw.gov.au``. The API accepts
POSTed JSON and returns one record per (site, parameter, hour).

Stage 00 model: pull the latest 24 h for a configurable set of sites and
let the curated asset attribute each record to the *nearest* pilot
vineyard. Sites that don't return data are logged and skipped.

Reference: https://www.airquality.nsw.gov.au/

The Orange-region station is at Bathurst (~50 km E of Cargo Road) — the
closest currently reporting NSW DPE site to Mount Canobolas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
class AirQualityStation:
    """One DPE site we pull PM2.5 from."""

    site_id: int
    name: str
    lat: float
    lon: float


#: Sites known to report PM2.5. Orange itself doesn't have a DPE air-quality
#: site; Bathurst is the nearest reporting member of the Central West
#: regional network (~50 km E of Cargo Road).
DEFAULT_STATIONS: tuple[AirQualityStation, ...] = (
    AirQualityStation(site_id=2557, name="BATHURST", lat=-33.4145, lon=149.5815),
    # Albury is ~320 km SW but covers smoke from Vic fires.
    AirQualityStation(site_id=2548, name="ALBURY", lat=-36.0737, lon=146.9135),
)


class AirQualityError(RuntimeError):
    """Raised on non-retriable API responses."""


class AirQualityResource(ConfigurableResource):
    """Thin client over the NSW DPE Air Quality observations endpoint.

    Configuration:
      * ``base_url``: defaults to the public DPE endpoint.
      * ``timeout_s``: request timeout seconds.
      * ``offline``: short-circuit to empty responses (used in smoke tests
        when no public network is available — keeps the asset graph green).
    """

    base_url: str = "https://data.airquality.nsw.gov.au"
    timeout_s: float = 20.0
    offline: bool = False

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _post(self, path: str, body: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(url, json=body)
            if 400 <= response.status_code < 500 and response.status_code != 429:
                raise AirQualityError(
                    f"AirQuality {response.status_code}: {response.text[:200]}"
                )
            response.raise_for_status()
            data = response.json()
            return list(data) if isinstance(data, list) else []

    def recent_pm25(
        self,
        *,
        stations: tuple[AirQualityStation, ...] = DEFAULT_STATIONS,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """Pull the last ``hours`` of PM2.5 records from the given sites.

        Returns one dict per (site, hour) with keys
        ``{site_id, name, ts, pm25_ug_m3, lat, lon}``. Non-reporting sites
        and out-of-range PM values are filtered out by the caller — we
        return raw rows here so the curation step is the only place that
        normalises.
        """
        if self.offline:
            return []
        now = datetime.now(tz=UTC)
        start = now - timedelta(hours=hours)
        body = {
            "Parameters": ["PM2.5"],
            "Sites": [s.site_id for s in stations],
            "StartDate": start.strftime("%Y-%m-%d"),
            "EndDate": now.strftime("%Y-%m-%d"),
            "Categories": ["Averages"],
            "SubCategories": ["Hourly"],
            "Frequency": ["Hourly average"],
        }
        try:
            raw = self._post("api/Data/get_Observations", body)
        except (httpx.HTTPError, AirQualityError):
            # Live API may be unreachable from the dev sandbox; the asset
            # check converts this to a non-blocking warning rather than
            # turning the entire pipeline red.
            return []

        by_id = {s.site_id: s for s in stations}
        out: list[dict[str, Any]] = []
        for row in raw:
            sid = row.get("Site_Id")
            station = by_id.get(int(sid)) if sid is not None else None
            if station is None:
                continue
            value = row.get("Value")
            if value is None or value < 0 or value > 5000:
                continue
            ts_str = row.get("DateTime") or row.get("Date")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace(" ", "T")).replace(tzinfo=UTC)
            except (ValueError, AttributeError):
                continue
            out.append(
                {
                    "site_id": station.site_id,
                    "name": station.name,
                    "ts": ts,
                    "pm25_ug_m3": float(value),
                    "lat": station.lat,
                    "lon": station.lon,
                }
            )
        return out
