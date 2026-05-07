"""Integration tests for the vineyards router against a real PostGIS DB.

These exercise the ``ST_X / ST_Y`` round-trip that the unit tests cannot —
this is the path that produced a 500 in the live smoke when shapely was
missing. Running these prevents that class of regression.

Requires: ``make up`` so the docker-compose Postgres is reachable.
Run with: ``pytest -m integration apps/api/tests``.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration

# Fixed test fixture: a vineyard at a known lat/lon. We insert it inside
# the test's rolled-back transaction, then assert the API returns it
# correctly. The unique slug avoids any clash with seeded data.
_TEST_SLUG = "_pytest_integration_cargo"
_TEST_LAT = -33.317
_TEST_LON = 148.957


async def _insert_test_vineyard(session: AsyncSession) -> int:
    result = await session.execute(
        text(
            """
            INSERT INTO vineyards (slug, name, region, centroid)
            VALUES (
                :slug, 'Pytest Cargo Road', 'Orange NSW',
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            )
            RETURNING id
            """
        ),
        {"slug": _TEST_SLUG, "lat": _TEST_LAT, "lon": _TEST_LON},
    )
    vineyard_id: int = result.scalar_one()
    await session.flush()
    return vineyard_id


async def test_list_vineyards_returns_postgis_centroid(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Confirms ST_X / ST_Y extract lon/lat correctly via the running router.

    Regression test for the shapely-import bug surfaced by the live smoke:
    the unit tests bypassed the router by constructing the response model
    directly with a dict; only an integration test exercises the WKB →
    lon/lat round-trip end-to-end.
    """
    await _insert_test_vineyard(db_session)

    response = await client.get("/v1/vineyards")
    assert response.status_code == 200
    payload = response.json()
    matches = [v for v in payload if v["slug"] == _TEST_SLUG]
    assert len(matches) == 1
    centroid = matches[0]["centroid"]
    assert centroid["lat"] == pytest.approx(_TEST_LAT, abs=1e-6)
    assert centroid["lon"] == pytest.approx(_TEST_LON, abs=1e-6)


async def test_get_vineyard_detail_returns_blocks(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vineyard_id = await _insert_test_vineyard(db_session)
    await db_session.execute(
        text(
            """
            INSERT INTO blocks (vineyard_id, name, cultivar, elevation_m, slope_deg)
            VALUES (:vid, 'Block A', 'Pinot Noir', 920.0, 6.0)
            """
        ),
        {"vid": vineyard_id},
    )
    await db_session.flush()

    response = await client.get(f"/v1/vineyards/{vineyard_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == _TEST_SLUG
    assert body["centroid"]["lat"] == pytest.approx(_TEST_LAT, abs=1e-6)
    assert len(body["blocks"]) == 1
    assert body["blocks"][0]["cultivar"] == "Pinot Noir"


async def test_get_vineyard_404_for_unknown_id(client: AsyncClient) -> None:
    # vineyards.id is SMALLINT (max 32767); use a value safely within range
    # that we know isn't seeded.
    response = await client.get("/v1/vineyards/30000")
    assert response.status_code == 404


async def test_health_ready_hits_db(client: AsyncClient) -> None:
    response = await client.get("/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
