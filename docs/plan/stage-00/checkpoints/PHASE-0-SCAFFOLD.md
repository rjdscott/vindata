# Stage 00 — scaffold checkpoint

Scope: everything that can be verified without bringing up the docker-compose
stack. The next checkpoint (`SMOKE.md`) is the live end-to-end run after
`bash scripts/smoke.sh`.

## What ran

| Suite | Tests | Pass | Coverage |
|---|---|---|---|
| `packages/agronomy` | 26 | 26 | **99%** (gate ≥90%) |
| `apps/api` | 11 | 11 | — |
| `apps/ingest` | 8 | 8 | — |
| `apps/web` (vitest) | 5 | 5 | — |
| **Total** | **50** | **50** | |

## Independent gates

- `pnpm --filter @vindata/web exec tsc --noEmit` → exit 0 (strict TS clean).
- `pnpm --filter @vindata/web exec vite build` → 709 modules, **402 KB gzip**.
- Dagster `Definitions` object loads with all three assets in the graph.
- FastAPI OpenAPI spec contains every route the typed client expects.

## What's verified by these tests

- **agronomy.frost**: Allen 1957 / Snyder & de Melo-Abreu equation; golden
  vectors match by hand; hypothesis confirms score is in [0,1] and monotone
  non-increasing in Tmin; cold-air drainage adjustment behaves correctly.
- **API contract**: routes `/v1/health`, `/v1/vineyards`, `/v1/vineyards/{id}`,
  `/v1/vineyards/{id}/scores`, `/v1/vineyards/{id}/forecast`. Settings parse
  from env. Pydantic schemas reject out-of-range values.
- **Ingest pipeline**: `_normalise_one` shape correct; missing variables
  filled with nulls; hours-since-sunset is non-negative for all 24 hours;
  asset graph has no cycles or missing deps.
- **Web**: AdvisoryBanner renders with required wording; LevelChip renders
  every frost level; format helpers localise to Australia/Sydney.

## What is NOT yet verified (deferred to live smoke)

- Open-Meteo HTTP fetch round-trip.
- MinIO put/get round-trip.
- Postgres + Timescale + PostGIS extensions actually load.
- Alembic migration `0001_initial` applies and downgrades cleanly.
- Dagster materialise produces non-zero rows in `weather_forecasts` and
  `agronomy_scores`.
- React SPA renders the frost chart from real data.

## To run the live smoke

```bash
make up
make migrate
make seed
make dagster-materialize
curl -s http://localhost:8000/v1/vineyards/1/scores?wedge=frost | jq length
open http://localhost:5173
```

Or one-shot: `bash scripts/smoke.sh`.
