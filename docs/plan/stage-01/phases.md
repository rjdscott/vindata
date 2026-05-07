# VinData — Stage 01 Phased Delivery

> **Companion to** [`architecture.md`](./architecture.md).
>
> **Assumption**: 1 staff engineer + ~0.5 FTE help. Total ≈ **17.5 person-weeks** (~4.5 calendar months end-to-end).
>
> Each phase is independently shippable and has objectively testable success criteria. A phase is "done" only when every success criterion is demonstrably met (logged in `docs/plan/stage-01/checkpoints/phase-{N}.md`, created at phase close).

---

## Phase 1 — Foundations (2 person-weeks)

**Goal.** Shippable monorepo, IaC, CI/CD, both clouds wired; deploy a "hello world" SPA + API + Lambda end-to-end.

**Deliverables.**
- pnpm + turborepo monorepo skeleton (`apps/`, `packages/`, `infra/`).
- **Terraform** (`infra/`) for AWS: VPC (2 AZ), RDS Postgres 16 + Timescale extension, S3 buckets (raw + curated + state), Cognito user pool, SES sandbox, IAM least-privilege roles, EventBridge bus.
- Cloudflare Pages + Workers via Terraform Cloudflare provider; custom domain.
- GitHub Actions OIDC → AWS (no long-lived keys); Sentry projects (web + api); preview deploys per PR.
- Stub `/v1/health` endpoint and a static SPA splash page.

**Dependencies.** None.

**Success criteria.**
- [ ] `terraform apply` from a clean state succeeds in < 15 min with no manual steps.
- [ ] `git push origin main` deploys API + SPA in < 8 min (measured from GitHub Actions run start).
- [ ] `GET /v1/health` returns 200 from Cloudflare edge with **p95 < 150 ms** over a 5-min synthetic test.
- [ ] RDS reachable **only** from VPC (no public endpoint, verified by `nc` from outside the VPC failing).
- [ ] PR preview deploy creates a unique URL and tears down on PR close.

---

## Phase 2 — Ingestion + raw lake (3 person-weeks)

**Goal.** All public sources land in S3 idempotently with observability.

**Deliverables.**
- Lambda container images per source: `bom_access_c`, `bom_access_g`, `bom_obs`, `silo`, `open_meteo`, `air_quality`, `firms`.
- EventBridge schedules:
  - ACCESS-C hourly · ACCESS-G 6 h · BoM obs every 10 min · SILO daily 06:00 AEST · FIRMS hourly · AirQuality every 15 min.
- Step Function `backfill_silo` covering 1989–2024 for the Orange tile.
- CloudWatch dashboard "Ingest" with per-source ingest count, lag, error rate; alarms on failure rate > 1 %/24 h.
- Structured JSON logs (`structlog`) with correlation IDs.
- Idempotency: object key includes a hash of source bytes + cycle; re-runs are no-ops.

**Dependencies.** Phase 1.

**Success criteria.**
- [ ] ACCESS-C ingest **p95 lag ≤ 5 min** versus source publish time, measured over 7 days.
- [ ] **30-day idempotency proof**: replay all schedules end-to-end; zero duplicate object writes (S3 `PutObject` count delta = 0).
- [ ] SILO Orange-tile backfill (1989–2024) completes in **≤ 2 h**.
- [ ] All ingest failures produce a Sentry event with source, cycle, and a downloadable raw payload pointer.
- [ ] PoC AWS run-rate **≤ A$60/mo** at the end of Phase 2 (verified via Cost Explorer).

---

## Phase 3 — Curation + serving DB (2.5 person-weeks)

**Goal.** Postgres + Timescale + PostGIS schema populated; vineyard/block geometries loaded; obs and forecasts queryable through the API.

**Deliverables.**
- Alembic migrations creating the schema in [`architecture.md` §A.3](./architecture.md#a3-serving-db-schema-postgres-16--timescale--postgis).
- Seed script for the **6 vineyards + their blocks** from `infra/seed/vineyards.geojson` (Cargo Road centroid placeholder `−33.317, 148.957`; the other 5 vineyard names + coordinates to be confirmed by the user before seeding).
- Curation Lambdas: read raw → transform to Parquet → write curated → upsert into Postgres with `ON CONFLICT DO UPDATE`.
- Glue crawler over `s3://vindata-curated/`; Athena workgroup with a 1 GB scan cap.
- Continuous aggregates `weather_obs_hourly`, `weather_obs_daily`, `agronomy_daily_max`.

**Dependencies.** Phase 2.

**Success criteria.**
- [ ] Hypertables `weather_observations` and `weather_forecasts` exist with **7 d chunks** (verified via `_timescaledb_catalog`).
- [ ] Query `last 72h forecast for Cargo Road` returns in **p95 ≤ 200 ms** under load (5 RPS for 60 s).
- [ ] PostGIS `ST_Contains` lookup of an observation point to a vineyard polygon is verified for all 6 vineyards.
- [ ] Glue catalog has **5 curated tables** (one per ingestion source family), each queryable via Athena.
- [ ] Schema migration is reversible (`alembic downgrade -1` succeeds on a populated DB).

---

## Phase 4 — Models + agronomy scoring (4 person-weeks)

**Goal.** All four wedges implemented in `packages/agronomy`; hindcast notebooks pass thresholds; scoring Lambda runs on EventBridge.

**Deliverables.**
- `packages/agronomy` — pure Python, **no AWS deps**, unit-tested with pytest, **≥ 85 % coverage** on model code.
  - `frost.py`, `disease/{dmcast,gubler_thomas,broome_botrytis}.py`, `smoke.py`, `phenology/{caffarra_eccel,gdd,fao56_eto,swb}.py`, `thresholds.py`, `version.py`.
- Hindcast Jupyter notebooks per wedge in `apps/ingest/notebooks/`, each persisting metrics as JSON to `s3://vindata-curated/validation/{wedge}/{model_version}.json`.
- `score_runner` Lambda: fan-out per vineyard hourly; writes to `agronomy_scores`.
- Model versioning (SemVer) bumped on any calibration change; `model_version` recorded with every score row.

**Dependencies.** Phase 3.

**Success criteria.**
- [ ] **Frost**: MAE ≤ 1.2 °C and hit-rate ≥ 0.8 / FAR ≤ 0.3 on Orange AWS 063303 daily Tmin 2019–2024 (`Tmin ≤ 0 °C` events).
- [ ] **Powdery mildew (Gubler-Thomas)** reproduces the UC IPM published example dataset to within **± 2 index points**.
- [ ] **Smoke-taint** dose replay flags **≥ 80 %** of days with documented PM2.5 > 200 µg·h post-veraison during the 2019–20 NSW events.
- [ ] **Phenology** budbreak MAE ≤ 5 days vs published Wine Australia / regional phenological observations 2010–2024.
- [ ] Every score row in `agronomy_scores` carries a non-null `model_version` and `inputs_jsonb`.

---

## Phase 5 — API + React dashboard + email alerts (3.5 person-weeks)

**Goal.** All 6 vineyards see a working dashboard; email alerts fire end-to-end.

**Deliverables.**
- React app (`apps/web`) — Vite + TS + TanStack Query + MapLibre GL + shadcn/ui + Recharts.
  - Pages: **Overview map**, **Vineyard detail** (forecast, scores, phenology), **Alerts inbox**, **Admin**.
  - Cognito hosted UI for auth.
  - Required `<AdvisoryBanner>` on every score-rendering page; ESLint rule enforces it.
- FastAPI on Lambda Web Adapter (`apps/api`) — all endpoints from [`architecture.md` §A.4](./architecture.md#a4-api-endpoints-fastapi--openapi-31--rbac-via-cognito-jwt) live behind JWT authoriser.
- Cloudflare Worker — edge cache (60 s) on `/forecast` and `/scores`, vary on JWT `sub`/role.
- SES templates (frost / disease / smoke); EventBridge **daily 06:00 AEST digest**; alert-trigger Lambda subscribed to `agronomy_scores` writes.

**Dependencies.** Phase 4.

**Success criteria.**
- [ ] SPA **TTI < 2 s on 4G** (Lighthouse mobile, cold load).
- [ ] Map renders all 6 vineyards + active alerts in **< 800 ms** after auth.
- [ ] Synthetic injected `frost_score = extreme` produces an SES email **within 60 s** end-to-end.
- [ ] **Lighthouse a11y ≥ 90** on Overview and Vineyard detail pages.
- [ ] Build fails if any rendered score view is missing `<AdvisoryBanner>` (verified by adding a violating page in CI and asserting failure).
- [ ] OpenAPI spec generated and committed; `packages/shared-types` regenerated automatically in CI.

---

## Phase 6 — Hardening & soft launch (2.5 person-weeks)

**Goal.** Launch to the 6 vineyards / ~15 users with monitoring, runbook, and cost guardrails.

**Deliverables.**
- CloudWatch + Sentry alerts paging the on-call engineer (PagerDuty optional; email-only acceptable at PoC).
- AWS Budgets: A$300/mo soft alert, A$500/mo hard cap (account-level Service Control Policy / billing alarm).
- OpenTelemetry traces from API + ingest Lambdas to AWS X-Ray.
- `docs/runbook.md` — operational playbooks for ingest failures, schema drift, RDS failover, Cognito recovery.
- `docs/data-licensing.md` and `docs/validation.md` finalised.
- Data-attribution page rendered in the SPA footer.
- T&Cs + privacy policy reviewed and live; user onboarding script.
- Backup verification: PITR enabled on RDS; nightly snapshot replicated to `ap-southeast-4`.

**Dependencies.** Phase 5.

**Success criteria.**
- [ ] **30-day uptime ≥ 99.5 %** measured by external synthetic on `/v1/health`.
- [ ] **5xx rate ≤ 0.5 %** of total API requests over the 30-day window.
- [ ] **Monthly bill ≤ A$400** at the end of the soft launch month.
- [ ] **Restore-from-snapshot drill** succeeds in **≤ 30 min RTO** (run once, recorded).
- [ ] All 15 users provisioned in Cognito; **each user has confirmed receipt of at least one digest email** (audit_log entry + manual check).
- [ ] Runbook tested by handing it to a peer engineer to resolve a synthetic ingest failure without help.

---

## Out of scope for Stage 01 (deferred to Phase 7+)

- Vendor station integrations (Davis WeatherLink, Sencrop, Pessl, Goanna/WISD).
- Disease ground-truth partnership with AWRI / NSW DPI.
- BoM commercial redistribution MOU.
- High-resolution downscaling (CNN / RainNet).
- SMS / PWA push / native mobile.
- Public marketing site, billing, multi-tenant self-onboarding.
- ML-trained ensemble / yield forecasting / satellite NDVI overlay.
- Domain co-founder hire (recorded as a business-side gate, not engineering).

---

## Stage 01 acceptance (overall)

Stage 01 is "done" when:

1. All six phase checkpoints (`docs/plan/stage-01/checkpoints/phase-1..6.md`) are checked off and committed.
2. The 6 pilot vineyards are receiving the daily digest email and no critical (P0/P1) bug is open for > 24 h.
3. The total AWS + Cloudflare run-rate over the soft-launch month is **≤ A$400**.
4. A post-mortem doc (`docs/plan/stage-01/retrospective.md`) is written: what hindcast skill we actually achieved per wedge, what we got wrong, and what Stage 02 should change.
