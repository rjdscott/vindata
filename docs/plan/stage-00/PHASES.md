# VinData — Stage 00 Phased Delivery

> Stage 00 is one continuous push to a working end-to-end thin slice (frost wedge for Cargo Road), measured against objective checkpoints. Total effort: **~5–7 person-days** for one staff engineer.
>
> Companion: [`ARCHITECTURE.md`](./ARCHITECTURE.md), [`LOCAL-DEV.md`](./LOCAL-DEV.md).

---

## Phase 0.1 — Repo bootstrap (0.5 day)

**Goal.** A monorepo a peer could clone and run `make up` against, end-to-end green.

**Deliverables.**
- `package.json` (root, pnpm workspaces) + `pnpm-workspace.yaml` + `turbo.json`.
- `pyproject.toml` (root, `uv` workspace) referencing `apps/api`, `apps/ingest`, `packages/agronomy`.
- `Makefile` with a self-documenting `help` target listing all commands.
- `.env.example` (copied to `.env` on first run by `make up`).
- `.editorconfig`, `.gitignore`, `.pre-commit-config.yaml` (ruff, prettier, end-of-file fixer, trailing whitespace, check-yaml, check-toml).
- `.github/workflows/ci.yml` (lint + typecheck + tests; Docker layer cache).

**Success criteria**
- [ ] `pnpm install` and `uv sync` both complete without errors.
- [ ] `make help` lists all targets with descriptions.
- [ ] `pre-commit run --all-files` passes from a clean checkout.

---

## Phase 0.2 — Docker Compose stack (1 day)

**Goal.** The full local stack stands up with `make up` and is observably healthy.

**Deliverables.**
- `docker-compose.yml` services: `postgres`, `minio`, `mc-init`, `mailhog`, `dagster-webserver`, `dagster-daemon`, `api`, `web`.
- Health checks on every long-running service; `depends_on: { condition: service_healthy }` wiring.
- Named volumes for postgres + minio data (survive restarts).
- A `vindata` user-defined bridge network.
- Init scripts:
  - `infra/local/postgres/init.sql` — extensions (pgcrypto, postgis, timescaledb).
  - `infra/local/minio/create-buckets.sh` (executed by `mc-init`).
- `Makefile` targets: `up`, `down`, `nuke` (volumes + containers), `logs`, `ps`, `psql`, `mc`.

**Success criteria**
- [ ] `make up` brings every service to `healthy` in ≤ 60 s on a warm cache.
- [ ] `make logs api` and `make logs ingest` both stream JSON-formatted logs.
- [ ] `make psql` opens an interactive shell into the PoC database.
- [ ] `make nuke && make up` is idempotent.

---

## Phase 0.3 — Schema, seed, and API skeleton (1 day)

**Goal.** The DB has the 6 vineyards + Cargo Road blocks; the API serves them.

**Deliverables.**
- Alembic migration `0001_initial.py` creating `vineyards`, `blocks`, `weather_forecasts` (hypertable), `agronomy_scores` (hypertable).
- `scripts/seed_db.py` idempotent seed for Cargo Road + 5 placeholder neighbours.
- `apps/api`: FastAPI app with structured logging (`structlog`), pydantic-settings config, SQLAlchemy 2.0 async engine, dependency-injected DB session, `/v1/health`, `/v1/vineyards`, `/v1/vineyards/{id}`.
- OpenAPI 3.1 spec auto-published at `/openapi.json`.
- `pytest` suite: at least one unit test (settings parsing) and one integration test (`GET /v1/vineyards` against a test DB via `pytest-postgresql`).

**Success criteria**
- [ ] `make seed` is idempotent; running twice doesn't duplicate rows.
- [ ] `curl localhost:8000/v1/vineyards | jq` returns 6 vineyards.
- [ ] `make test-api` passes.
- [ ] OpenAPI spec validates with `swagger-cli validate`.

---

## Phase 0.4 — `packages/agronomy` frost model (1 day)

**Goal.** A pure-Python library implementing the frost model with literature citations and rigorous tests.

**Deliverables.**
- `packages/agronomy/src/agronomy/frost.py`:
  - Pure functions, no I/O, no globals, complete type hints.
  - `predict_tmin(forecast: ForecastWindow, params: FrostParams) -> TminPrediction`.
  - `score_from_tmin(tmin_c: float) -> FrostScore`.
  - Dataclasses for inputs/outputs (frozen, slotted).
- `packages/agronomy/src/agronomy/version.py` exports `MODEL_VERSION = "frost@0.1.0"`.
- `packages/agronomy/tests/test_frost.py`:
  - Property-based tests with `hypothesis` (e.g., score is monotone non-increasing in `tmin_c`).
  - Golden-vector tests (3 hand-computed cases from FAO Frost Protection examples).
- `ruff` and `mypy --strict` clean.
- Doc-comments cite Allen 1957 / Snyder & de Melo-Abreu 2005.

**Success criteria**
- [ ] `pytest packages/agronomy --cov=agronomy --cov-fail-under=90` passes.
- [ ] `mypy --strict packages/agronomy/src` passes.
- [ ] `ruff check packages/agronomy` passes.

---

## Phase 0.5 — Dagster ingest + scoring assets (1.5 days)

**Goal.** Hourly forecast lands in MinIO + Postgres, and scoring runs as a downstream asset.

**Deliverables.**
- `apps/ingest/src/vindata_ingest/`:
  - **Resources**: `MinioResource`, `PostgresResource`, `HttpResource` (httpx with retry/backoff via `tenacity`). All resources have `.health()` methods used by Dagster's `check_assets`.
  - **Assets**:
    1. `raw_open_meteo_forecast` — partitioned daily, materialises a JSON blob to MinIO at `s3://vindata-raw/open_meteo/dt=YYYY-MM-DD/cycle=HH/{vineyard_slug}.json`. Idempotent (overwrites same key for same partition).
    2. `curated_forecast` — reads raw, normalises into a Polars DataFrame, writes Parquet to `s3://vindata-curated/forecast/...`, upserts into Postgres `weather_forecasts`.
    3. `frost_score` — depends on `curated_forecast`; computes per-`valid_ts` score using `packages/agronomy.frost`; upserts into `agronomy_scores`.
  - **Schedule**: hourly on the top of the hour.
  - **Sensor**: backfill if any partition is missing in the last 48 h.
  - **Asset checks** (Dagster v1.7+): non-null `t2m`, sane ranges (`-30 < t2m < 50`), monotone `valid_ts`.
- Dagster code-locations file `workspace.yaml` referencing `vindata_ingest.definitions:defs`.

**Success criteria**
- [ ] `make dagster-materialize` runs all assets to green.
- [ ] After a successful run, `select count(*) from weather_forecasts` ≥ 72 (hourly × 3 days × 6 vineyards) and `select count(*) from agronomy_scores where wedge='frost'` ≥ 72.
- [ ] Asset checks pass; one deliberately-broken input causes the corresponding check to FAIL (proving they actually run).
- [ ] Re-materialising the same partition twice produces the same output (idempotency).

---

## Phase 0.6 — React SPA: map + frost detail (1 day)

**Goal.** A clean, minimal UI showing all 6 vineyards on a map and a frost forecast chart for any vineyard.

**Deliverables.**
- `apps/web` (Vite + TS strict mode + React 18):
  - **Routing**: TanStack Router (file-based, type-safe).
  - **Data fetching**: TanStack Query against the typed client generated from `/openapi.json`.
  - **Styling**: Tailwind v4 + shadcn/ui + lucide-react icons.
  - **Map**: MapLibre GL with OSM raster tiles (no API key); markers for the 6 vineyards.
  - **Charts**: Recharts area chart of `t2m` + line of `Tmin_pred` over the 72 h horizon, with frost-level bands shaded.
  - **Pages**: `OverviewPage` (map + alerts panel), `VineyardPage` (forecast + frost chart + raw forecast table).
  - **Components**: `<AdvisoryBanner>` rendered in a layout wrapper that wraps every score-rendering page.
  - **Lint guard**: a project-local ESLint rule (`no-unwrapped-score`) fails the build if a render of `agronomy_scores` is missing the banner.
- Generated client at `apps/web/src/api/client.ts` regenerated by `make gen-types`.

**Success criteria**
- [ ] `pnpm --filter web build` produces a clean production bundle ≤ 500 KB gzip.
- [ ] Lighthouse: Performance ≥ 90, Accessibility ≥ 90 on `OverviewPage`.
- [ ] Removing `<AdvisoryBanner>` from a layout fails the build.

---

## Phase 0.7 — End-to-end smoke (0.5 day)

**Goal.** Validate the whole pipeline as one flow.

**Deliverables.**
- `scripts/smoke.sh`:
  1. `make nuke && make up`
  2. wait until all healthchecks green
  3. `make seed`
  4. `make dagster-materialize` (or wait for the schedule)
  5. assert `GET /v1/vineyards/{cargo-road-id}/scores?wedge=frost` returns ≥ 72 rows
  6. open `http://localhost:5173/vineyards/cargo-road` (printed link, not auto-opened)
- `docs/plan/stage-00/checkpoints/SMOKE.md` records: timestamp, frost score samples, screenshot path.

**Success criteria**
- [ ] `bash scripts/smoke.sh` exits 0.
- [ ] Browser shows a frost chart with at least one non-zero score.
- [ ] No errors in Dagster, API, or web logs during the smoke run.

---

## Done means

Stage 00 is "done" when `bash scripts/smoke.sh` exits 0 from a clean checkout on a peer's laptop. The artifact set:

1. The four Stage 00 docs in `docs/plan/stage-00/`.
2. The runnable monorepo (Phases 0.1–0.7).
3. `docs/plan/stage-00/checkpoints/SMOKE.md` proving the smoke ran green.
4. `docs/plan/stage-00/checkpoints/RETRO.md` — what we'd do differently in Stage 01.
