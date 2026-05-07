# Stage 00 — Live smoke retrospective

> **Run date**: 2026-05-07.
> **Outcome**: green. `bash scripts/smoke.sh` exits 0; `GET /v1/vineyards/1/scores?wedge=frost` returns 71 rows; React SPA renders the frost forecast for Cargo Road.
>
> **Why this doc exists**: the entire premise of Stage 00 (vs. cloud-first) is that bringing up the full pipeline on a laptop surfaces production-class bugs *cheaply*. Five real bugs were found and fixed during the smoke. Each one would have been a half-day fire-drill against AWS Lambda + RDS where iteration is slow. This doc records each bug, its root cause, and the durable fix in the repo, so the value of Stage 00 is auditable.

## Counts

- 5 production-class bugs caught by the smoke
- 6 service containers stood up (postgres, minio, mailhog, api, dagster-webserver, dagster-daemon, web)
- 6 vineyards seeded
- 432 forecast rows ingested (6 × 72 h)
- 71 frost scores produced (some Open-Meteo edge-of-horizon nulls were skipped, as designed)
- 4 separate test suites (agronomy, api, ingest, web): **52 unit tests + 4 integration tests + 2 ESLint rule tests = 58 tests, all green**

## Bug 1 — Dagster's internal `alembic_version` colliding with the application's

**Symptom**
On first `make up`, `vindata-dagster-webserver` failed its healthcheck. Its
logs showed:

```
alembic.util.exc.CommandError: Can't locate revision identified by '0001_initial'
```

`0001_initial` is the application's own Alembic revision ID — not a
revision Dagster's internal migration tree contains.

**Root cause**
Dagster keeps run / event / schedule storage in Postgres, and on startup
it runs *its own* internal Alembic migrations. We had pointed Dagster at
the `vindata` database — the same one the API had already migrated. Both
systems wanted to manage the same `alembic_version` row.

**Fix**
1. `infra/local/postgres/init.sql` now also creates a separate `dagster`
   database on first volume creation:
   ```sql
   SELECT 'CREATE DATABASE dagster OWNER vindata'
   WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'dagster')
   \gexec
   ```
2. `infra/local/dagster/dagster.yaml` (host-mounted into both Dagster
   services — see Bug 2) sets `db_name: dagster`.

The two systems now own independent schemas. Stage 01's IAM-isolated
RDS instances make this collision impossible by construction.

## Bug 2 — Docker layer cache hiding a `dagster.yaml` config change

**Symptom**
The fix for Bug 1 was applied to `apps/ingest/Dockerfile` (a `RUN printf
'…' > dagster.yaml` line). The next `make up` rebuilt nothing visible,
but the dagster.yaml inside the running container *still showed the old
content* (`db_name: vindata`). The bug from #1 reproduced.

**Root cause**
`docker compose up` does not pass `--build` by default. Even when it does
build, Docker's layer cache compared file contents in the COPY-ed source
tree, not the literal `RUN printf` command's bytes. The `dagster.yaml`
that the printf produced was baked into a layer that the cache reused.

**Fix**
1. Pulled `dagster.yaml` out of the Dockerfile entirely. It now lives at
   `infra/local/dagster/dagster.yaml`.
2. Both Dagster services bind-mount it at `/opt/dagster/dagster_home/
   dagster.yaml` in `docker-compose.yml`.
3. Removed the `dagster-home` named volume from compose (it was shadowing
   the bind-mount).
4. `make up` now uses `docker compose up -d --build --wait`, so any
   future Dockerfile change always rebuilds.

Single-source-of-truth, on the host, no layer-cache surprises.

## Bug 3 — IPv6 / IPv4 mismatch on `web` healthcheck

**Symptom**
After Bug 2 was fixed, every other service came up healthy but `web`
sat at `health: starting` indefinitely. Vite logs clearly said
`Local: http://localhost:5173/` and a manual `wget` to that URL from
the host returned the SPA. The healthcheck still wouldn't go green.

**Root cause**
The healthcheck command was `wget -q --spider http://localhost:5173`.
Inside an Alpine container, `localhost` resolves to `::1` (IPv6) first.
Vite (started with `--host 0.0.0.0`) was bound to `0.0.0.0:5173` —
IPv4 only. `wget` tried `::1`, got `Connection refused`, and never
fell back to IPv4.

**Fix**
Healthcheck now uses `127.0.0.1` explicitly:

```yaml
test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1:5173/ || exit 1"]
```

A small comment in `docker-compose.yml` records *why* — `localhost`
would not work.

## Bug 4 — PostgreSQL forbids NULL in PK columns; `block_id` must be nullable

**Symptom**
After Bug 3 was fixed and the stack stood up clean, `make seed` ran fine
but `dagster asset materialize` failed on `frost_score` with:

```
psycopg.errors.NotNullViolation:
  null value in column "block_id" of relation "_hyper_2_3_chunk"
  violates not-null constraint
```

**Root cause**
The `agronomy_scores` table's primary key was a composite of
`(vineyard_id, wedge, ts, lead_h, block_id)`. The Stage 00 frost wedge
scores at the *vineyard* level (no specific block), so `block_id`
needed to be `NULL` for those rows. PostgreSQL forbids `NULL` in any
primary-key column — in violation of the column being formally
declared nullable elsewhere.

**Fix**
Re-modelled `agronomy_scores`:

1. Surrogate `id BIGINT IDENTITY` primary key.
2. The natural key is enforced by a `UNIQUE NULLS NOT DISTINCT` constraint
   (PostgreSQL 15+) named `pk_agronomy_scores`, which is the conflict
   target the scoring asset's upsert references.
3. Dropped the TimescaleDB hypertable on this table — Stage 00 volumes
   don't justify partitioning, and TimescaleDB requires the partition
   column in any unique constraint, which conflicts with the surrogate
   PK approach. We can convert later when volumes warrant it.

Migration is in `apps/api/alembic/versions/0001_initial.py`. Model is in
`apps/api/src/vindata_api/models/__init__.py`.

`weather_forecasts` (which has a non-null natural key on
`(vineyard_id, model, init_ts, valid_ts)`) remains a hypertable,
unchanged.

## Bug 5 — Missing `shapely` produced a 500 from `/v1/vineyards`

**Symptom**
After Bug 4 was fixed and the smoke went green (71 frost scores returned
correctly), opening the SPA at `localhost:5173` showed:

> Failed to load vineyards: Failed to fetch

**Root cause**
The vineyards router used `geoalchemy2.shape.to_shape(centroid)` to
convert the PostGIS WKB blob to a shapely Point so the lat/lon could be
extracted. `geoalchemy2`'s shape helpers are only imported at *runtime*
when called — `to_shape` raises an `ImportError` from inside the router
if `shapely` isn't installed. The API container's deps did not include
`shapely`.

The unit tests didn't catch this because they constructed
`VineyardSummaryResponse` directly with a dict, bypassing the router
entirely. Only an end-to-end request against a real PostGIS column
exercises this path.

**Fix**
1. Removed the `geoalchemy2.shape` dependency. The router now extracts
   `lat` / `lon` in SQL using `ST_X / ST_Y` against the geography cast
   to geometry. This is faster (one round-trip), avoids the dep, and
   works identically against RDS PostGIS in Stage 01.
2. **Added an integration test** (`apps/api/tests/
   test_vineyards_integration.py`) that hits the running compose
   Postgres and exercises the WKB → lat/lon round-trip. This class of
   bug is now impossible to ship: `pytest -m integration` fails before
   the change reaches the smoke. The test is auto-skipped in default
   `pytest` runs (no live DB), so unit-only CI stays fast.

## Lessons

| Lesson | Where it landed |
|---|---|
| Multi-tenant Postgres needs schema/database isolation, not "everyone shares one DB" | Stage 01 already plans separate RDS instances per major service |
| Don't bake mutable config into Docker images; bind-mount it from the host | Pattern in `docker-compose.yml` for any future config |
| Always specify `127.0.0.1` over `localhost` in container healthchecks | `docker-compose.yml` carries a comment explaining why |
| PostgreSQL won't let you put `NULL` in a PK; use a surrogate + `UNIQUE NULLS NOT DISTINCT` | `0001_initial.py` is the canonical example for future tables |
| Optional library imports must be installed or routed around — runtime `ImportError` is invisible until you exercise the path | Integration tests (Bug 5 fix) are now first-class |
| `make smoke` is **the** test that mattered — half the failures above were invisible to unit tests | Stage 00 architecture is validated; Stage 01 keeps the smoke as a checkpoint |
