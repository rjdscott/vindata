"""Open-Meteo client.

Stage 00 source. Free, no API key, JSON. The class is intentionally a thin
wrapper so swapping in BoM ACCESS-C in Stage 01 means a sibling resource and
a different asset; the curation asset stays the same shape.
"""

from __future__ import annotations

from typing import Any

import httpx
from dagster import ConfigurableResource
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class OpenMeteoError(RuntimeError):
    """Raised on non-retriable API responses."""


class OpenMeteoResource(ConfigurableResource):
    base_url: str
    timeout_s: float = 15.0

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get(url, params=params)
            if 400 <= response.status_code < 500 and response.status_code != 429:
                # Don't retry client errors except rate limits.
                raise OpenMeteoError(
                    f"Open-Meteo {response.status_code}: {response.text[:200]}"
                )
            response.raise_for_status()
            return response.json()

    def hourly_forecast(
        self,
        *,
        lat: float,
        lon: float,
        forecast_days: int = 3,
        timezone: str = "Australia/Sydney",
    ) -> dict[str, Any]:
        """Pull hourly forecast for one location.

        Returns the parsed JSON. Includes the variables ``agronomy.frost``
        consumes: temperature_2m, dew_point_2m, relative_humidity_2m,
        wind_speed_10m, wind_direction_10m, precipitation, cloud_cover,
        shortwave_radiation.
        """
        params: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(
                [
                    "temperature_2m",
                    "dew_point_2m",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "precipitation",
                    "cloud_cover",
                    "shortwave_radiation",
                ]
            ),
            "forecast_days": forecast_days,
            "timezone": timezone,
            "wind_speed_unit": "ms",
            "timeformat": "iso8601",
        }
        return self._get("forecast", params)
