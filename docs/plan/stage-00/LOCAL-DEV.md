# VinData — Stage 00 Local Development Guide

## Prerequisites

| Tool | Min version | Reason |
|---|---|---|
| Docker Desktop / Engine | 24+ | Compose v2 (file format `compose-spec`). |
| Docker Compose | v2.20+ | `--wait` and depends_on health gates. |
| Node | 22.x | Active LTS. |
| pnpm | 9.x | Workspaces, deterministic installs. Activate via `corepack enable && corepack prepare pnpm@9 --activate`. |
| Python | 3.12 | Match container runtime; type hints with `|` syntax. |
| `uv` | 0.4+ | Python deps + venvs. |
| `make` | any | Canonical task runner. |
| `pre-commit` | latest | Installed via `uv tool install pre-commit`. |

> **No global Python installs.** All Python deps go via `uv` into per-package venvs (`.venv/` is gitignored). The same lockfile drives the Dockerfiles via `uv pip sync uv.lock`.

## First-time setup

```bash
git clone <repo>
cd vindata

# Once
corepack enable && corepack prepare pnpm@9 --activate
uv tool install pre-commit
pre-commit install --install-hooks

# Bootstrap deps
pnpm install
uv sync                 # hydrates each Python workspace

# Bring up the stack
cp .env.example .env    # `make up` does this if .env is missing
make up                 # waits for all healthchecks; ≤ 60 s on warm cache
make seed               # idempotent; loads 6 vineyards
make dagster-materialize  # runs the asset graph end-to-end
open http://localhost:5173        # the app
open http://localhost:3001        # Dagster UI
open http://localhost:9001        # MinIO console (login from .env)
open http://localhost:8025        # MailHog UI (no alerts at Stage 00 yet)
```

## Make targets

```
make help                 # list all targets
make up                   # docker compose up -d --wait
make down                 # docker compose down
make nuke                 # down + remove volumes (destructive)
make logs <svc>           # follow logs for one service
make ps                   # docker compose ps
make psql                 # interactive psql into the PoC DB
make mc                   # MinIO Client shell against local MinIO
make seed                 # python scripts/seed_db.py
make gen-types            # API openapi.json -> apps/web typed client
make dagster-materialize  # one-shot materialise all assets
make hindcast             # python scripts/hindcast_frost.py
make test                 # all tests (api + agronomy + web)
make test-api             # pytest in apps/api
make test-agronomy        # pytest in packages/agronomy
make test-web             # vitest in apps/web
make lint                 # ruff + eslint + prettier --check
make fmt                  # ruff format + prettier --write
make typecheck            # mypy --strict (python) + tsc --noEmit (ts)
make smoke                # scripts/smoke.sh, full e2e
```

## Service URLs

| Service | URL | Notes |
|---|---|---|
| Web (Vite) | http://localhost:5173 | Hot-reload. |
| API (FastAPI) | http://localhost:8000 | `/docs` for Swagger UI; `/openapi.json` for spec. |
| Dagster | http://localhost:3001 | Asset graph + run history. |
| MinIO console | http://localhost:9001 | User/pass from `.env`. |
| MinIO API (S3) | http://localhost:9000 | boto3 `endpoint_url`. |
| MailHog | http://localhost:8025 | SMTP capture. |
| Postgres | `postgres://vindata:vindata@localhost:5432/vindata` | TimescaleDB + PostGIS. |

## Conventions (so the codebase stays clean as it grows)

### Python

- **Package manager**: `uv` (no pip, no Poetry). Workspaces declared in root `pyproject.toml`.
- **Linter / formatter**: `ruff` (replaces black, isort, flake8). Config in root `pyproject.toml`.
- **Type checker**: `mypy --strict` for `apps/api` and `packages/agronomy`; `mypy` (non-strict) for `apps/ingest` (Dagster's typing isn't fully strict-clean yet).
- **Testing**: `pytest` + `pytest-asyncio` + `pytest-postgresql` + `hypothesis`. Coverage gate: ≥ 90% on `packages/agronomy`, ≥ 70% on `apps/api`.
- **Logging**: `structlog`, JSON renderer in containers, console renderer in tests. No `print()`.
- **Settings**: `pydantic-settings` with `env_prefix` per app (`VINDATA_API_…`).
- **HTTP**: `httpx` + `tenacity` retry decorator (exponential backoff, max 3 attempts, jittered). Timeout always set explicitly.
- **DB**: SQLAlchemy 2.0 with `Mapped[…]` typed ORM; async engine via `asyncpg`. Alembic for migrations.

### TypeScript / React

- **Package manager**: `pnpm` workspaces.
- **Build**: Vite + `vite-plugin-checker` (runs `tsc --noEmit` and ESLint in dev).
- **Linter**: ESLint flat config (`eslint.config.js`) with `@typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-import`, `eslint-plugin-jsx-a11y`. Custom rule `no-unwrapped-score` enforces `<AdvisoryBanner>`.
- **Formatter**: Prettier.
- **Types**: `strict: true`, `noUncheckedIndexedAccess: true`, `noImplicitOverride: true`.
- **Data fetching**: TanStack Query; query keys are tuples derived from a `keys.ts` factory (no string-typed keys scattered).
- **API client**: generated from `/openapi.json` by `openapi-typescript`. Hand-edited types are forbidden by CI.
- **Components**: `shadcn/ui` primitives composed; no custom design system at PoC.
- **Testing**: `vitest` + `@testing-library/react` for components; `playwright` only when needed (not at Stage 00).

### Cross-cutting

- **Pre-commit hooks** (gating): ruff, ruff-format, prettier, eof-newline, trailing-whitespace, check-yaml, check-toml, no-large-files (10 MB limit on data/).
- **Conventional commits** suggested but not enforced at PoC.
- **Branching**: trunk-based; PRs squash-merge into `main`.
- **CI**: GitHub Actions running `make lint typecheck test` on every push. Cached pnpm + uv stores.

## Troubleshooting

- **`make up` hangs on `dagster-webserver healthy`** — check `make logs dagster-webserver`. Most common cause: code-location import error in `vindata_ingest.definitions`.
- **Postgres healthy but API can't connect** — check `VINDATA_API_DATABASE_URL` matches the compose service host (`postgres`, not `localhost`, from inside containers).
- **MinIO "Access Denied" from boto3** — `endpoint_url` must be `http://minio:9000` (in-network) or `http://localhost:9000` (host).
- **Open-Meteo 429** — the public API rate-limits; the `HttpResource` retries with backoff, but heavy `make hindcast` runs may need to throttle further.
- **`make nuke` then `make up` fails** — run `docker volume ls | grep vindata` to confirm volumes are gone; `docker compose down -v` if any survived.
