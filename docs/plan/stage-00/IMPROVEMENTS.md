# Stage 00 — Improvements over the original research doc

> The research doc (`docs/vindata-research-claude-01.md`) is a strong strategic brief. The Stage 01 plan already carries forward its red flags as constraints. Stage 00 makes some additional pragmatic departures, listed here so the choices are auditable.

## 1. Open-Meteo as the Stage 00 forecast source — *not* BoM ACCESS-G/C

**Research doc says**: ingest BoM ACCESS-G + ACCESS-C GRIB2 directly.

**Stage 00 says**: use Open-Meteo (`/v1/forecast` and `/v1/archive`) as the only forecast source until we hit AWS.

**Why**:
- BoM GRIB2 needs `cfgrib` + `eccodes` native libs. On a developer laptop that's a 2–3 day yak shave; in a Lambda container it's worse. The PoC shouldn't pay that tax.
- Open-Meteo exposes the same variables we need (T, dewpoint, RH, wind, cloud, solar radiation) as JSON over plain HTTPS — zero native deps.
- Source coupling is hidden behind an `assets/raw_open_meteo_forecast` Dagster asset. Replacing it with `assets/raw_bom_access_c` in Stage 01 leaves the rest of the graph unchanged.

**Cost**: Open-Meteo's free tier is non-commercial. Documented in `docs/data-licensing.md`. Stage 01 swaps the source before any commercial launch.

## 2. Dagster software-defined assets, not EventBridge + Step Functions

**Research doc says**: EventBridge cron + Lambda + Step Functions for backfills.

**Stage 00 says**: Dagster software-defined assets, with the same orchestrator carried into Stage 01.

**Why**:
- The orchestration *is* the data lineage. SDAs make that explicit; cron + Lambda hides it across many configs.
- Local dev UX is incomparable: a single `dagster dev` command shows the full DAG, run history, partition status, asset checks.
- Backfills are a first-class operation in Dagster; in Step Functions they're a separate state machine you write by hand.
- Migrating to AWS is not a rewrite: Dagster runs on ECS Fargate, EKS, or Dagster Cloud. The asset definitions are unchanged.

## 3. Single Postgres for everything (no lakehouse at PoC)

**Research doc says**: Iceberg-on-S3 lakehouse with Postgres for serving.

**Stage 00 says**: just Postgres + Timescale + PostGIS. Parquet in MinIO is for *raw lineage* only, not querying.

**Why**:
- 6 vineyards × 168 forecast hours × hourly cycles ≈ 7,250 rows/day. Postgres laughs at this.
- Iceberg's value (atomic snapshots, time travel, schema evolution) doesn't pay for its complexity until you have multiple compute engines or > 1 TB.
- Stage 01 may add Athena over curated Parquet for ad-hoc analysis. Stage 00 doesn't need it.

## 4. `uv` for Python, not pip / Poetry / pip-tools

**Research doc**: silent on Python tooling.

**Stage 00**: `uv` end-to-end (workspace declared in root `pyproject.toml`).

**Why**:
- 10–100× faster installs. Materially affects CI and Docker layer rebuild times.
- Single tool covers venvs, lockfiles, project resolution, tool installs.
- `uv sync` in the Dockerfile uses the same `uv.lock` as local dev, eliminating the "works on my machine" gap.

## 5. No auth at Stage 00

**Research doc / Stage 01**: Cognito.

**Stage 00**: a single `current_user` FastAPI dependency that returns a hardcoded admin user.

**Why**:
- The 6 pilot vineyards are not on the laptop. Auth is a Stage 01 concern.
- The seam is the only thing that matters: when Stage 01 swaps Keycloak/Cognito in, only `apps/api/src/vindata_api/deps.py:current_user` changes.

## 6. Frost wedge ships first; the other three follow in Phase 0.8

**Research doc / Stage 01**: all four wedges (frost, disease, smoke, phenology) at MVP.

**Stage 00 thin slice (Phases 0.1–0.7)**: frost only, end-to-end.

**Stage 00 expansion (Phase 0.8 — landed in PR #2)**: all four wedges shipped end-to-end; NSW DPE Air Quality and NASA FIRMS wired as real public-data sources; dashboard refactored to a 4-card grid; hindcast against 8 years of SILO Orange tile.

**Why phased rather than all-at-once**:
- Frost was the simplest of the four (no LWD inference, no BBCH gate, no PM2.5 fusion). Shipping it first proved the *pipeline* could be exercised on a single wedge.
- The other three then dropped in mechanically once the schema, asset graph, scoring contract, and dashboard shell were proven. Phase 0.8 added ~7,500 lines (model code + tests + ingestors + cards) over ~1.5 days.
- Validation is honest: `packages/agronomy/notebooks/hindcast.py` runs all four wedges against real SILO data and reports metrics (frost MAE, hit-rate; phenology budbreak DOY; smoke flag-rate on Black Summer; disease event counts). Stage 01 acceptance bands are not yet met for frost / phenology — refitting on Orange BoM AWS 063303 is genuine Stage 01 work, not a Stage 00 oversight.

## 7. OpenAPI-generated TypeScript client

**Research doc**: silent on API contract management.

**Stage 00**: `apps/web/src/api/client.ts` is generated from `apps/api`'s OpenAPI spec. CI fails if the generated file drifts.

**Why**:
- The class of bugs where the API and UI disagree on a field name costs a 30-minute round trip per occurrence. Generated types make it impossible.
- The OpenAPI spec is the single source of truth for the contract; treat it like any other compiled artifact.

## 8. Pre-commit hooks gating commits

**Research doc**: silent on local quality gates.

**Stage 00**: `.pre-commit-config.yaml` runs ruff, prettier, eof-newline, etc. on every commit.

**Why**:
- Ten minutes of one-time setup removes a year's worth of PR review noise.
- Aligning local format with CI eliminates the "fix lint" commit class entirely.

## 9. Industry-best-practice toolchain (vs the research doc's loose recommendations)

| Concern | Research doc | Stage 00 | Why |
|---|---|---|---|
| Python lint/format | unspecified | `ruff` + `ruff format` | One tool replaces black, isort, flake8, pylint. ~50× faster. |
| Python types | unspecified | `mypy --strict` (api, agronomy) | Catches the bugs that break demos. |
| Python HTTP | unspecified | `httpx` + `tenacity` | `requests` is unmaintained for retries; `httpx` is the modern default. |
| Python DB | "PostgreSQL+TimescaleDB" | SQLAlchemy 2.0 typed ORM + Alembic + asyncpg | Typed `Mapped[…]` columns; async I/O for the API. |
| TS lint | unspecified | ESLint flat config + custom `no-unwrapped-score` rule | Enforces the Advisory framing in code, not in code review. |
| TS routing | unspecified | TanStack Router (file-based, type-safe) | Routes are a contract, not a string. |
| TS data fetching | unspecified | TanStack Query | The standard. |
| TS dataframe / charts | unspecified | Recharts | Sane defaults; Tailwind-friendly. |
| Map | "MapLibre GL" | MapLibre + OSM raster | Free, no API key. |
| Task runner | npm scripts | `make` (with self-documenting `help`) | Language-agnostic, single discoverable surface. |
| CI | "GitHub Actions" | matrixed `make lint typecheck test`, layered cache | Same commands locally and in CI. |
| Commits | unspecified | Conventional Commits suggested | Cleaner changelog later. |

## 10. Things deliberately *not* added vs the research doc

We resisted the temptation to:

- **Add a feature store** (Feast/Tecton). Premature for 6 vineyards.
- **Add Iceberg** at PoC. See §3.
- **Add Kafka / Kinesis**. Open-Meteo is request-pull. There is nothing to stream.
- **Add a separate "ML platform"** (Modal/Replicate). The agronomy "models" at PoC are deterministic functions, not learned models.
- **Add multi-tenant scaffolding**. Six vineyards, one tenant, hardcoded.

Each addition above can be motivated later when the data justifies it. Adding any of them now would slow the PoC and obscure where the actual difficulty lies (the agronomy models and their validation).
