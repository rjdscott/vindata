"""App-construction smoke: ensures wiring is sound without a live DB.

We assert the OpenAPI document is generated and contains the expected paths.
This is the contract apps/web's typed client depends on; if a route name
drifts, this test fails before integration.
"""

from __future__ import annotations

from vindata_api.main import create_app
from vindata_api.settings import Settings


def test_openapi_paths_contain_expected_routes() -> None:
    app = create_app(Settings(_env_file=None))
    spec = app.openapi()
    assert "/v1/health" in spec["paths"]
    assert "/v1/vineyards" in spec["paths"]
    assert "/v1/vineyards/{vineyard_id}" in spec["paths"]
    assert "/v1/vineyards/{vineyard_id}/scores" in spec["paths"]
    assert "/v1/vineyards/{vineyard_id}/forecast" in spec["paths"]


def test_openapi_version_is_3_1() -> None:
    app = create_app(Settings(_env_file=None))
    spec = app.openapi()
    assert spec["openapi"].startswith("3.1")
