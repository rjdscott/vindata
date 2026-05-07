# VinData — canonical task runner.
# Discoverable: `make help`. All targets are language-agnostic so a peer engineer
# can drive the project without knowing pnpm or uv.

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

# Detect docker compose v2 plugin vs legacy.
COMPOSE := docker compose

# -----------------------------------------------------------------------------
# Help — self-documenting via "## Description" comments next to each target.
# -----------------------------------------------------------------------------
.PHONY: help
help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# -----------------------------------------------------------------------------
# Stack lifecycle
# -----------------------------------------------------------------------------
.PHONY: env
env: ## Create .env from .env.example if missing.
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

.PHONY: up
up: env ## Bring the full local stack up (waits for healthchecks). Builds first so Dockerfile changes always take effect.
	$(COMPOSE) up -d --build --wait
	@echo
	@echo "Stack is up. URLs:"
	@echo "  Web        http://localhost:5173"
	@echo "  API        http://localhost:8000  (docs: /docs, spec: /openapi.json)"
	@echo "  Dagster    http://localhost:3001"
	@echo "  MinIO UI   http://localhost:9001  (console)"
	@echo "  MailHog    http://localhost:8025"

.PHONY: down
down: ## Stop the stack (volumes preserved).
	$(COMPOSE) down

.PHONY: nuke
nuke: ## Stop the stack and remove volumes (destructive).
	$(COMPOSE) down -v

.PHONY: ps
ps: ## Show service status.
	$(COMPOSE) ps

.PHONY: logs
logs: ## Tail logs for one service: make logs <svc> or make logs (all).
	@if [ -z "$(filter-out logs,$(MAKECMDGOALS))" ]; then \
	  $(COMPOSE) logs -f --tail=200; \
	else \
	  $(COMPOSE) logs -f --tail=200 $(filter-out logs,$(MAKECMDGOALS)); \
	fi
%:
	@:

.PHONY: psql
psql: ## Open psql against the local DB.
	$(COMPOSE) exec postgres psql -U vindata -d vindata

.PHONY: mc
mc: ## Open MinIO Client (mc) shell against the local MinIO.
	$(COMPOSE) run --rm mc-init sh

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------
.PHONY: migrate
migrate: ## Run Alembic migrations against the local DB.
	$(COMPOSE) exec api alembic upgrade head

.PHONY: seed
seed: ## Seed the 6 vineyards (idempotent).
	$(COMPOSE) exec api python -m vindata_api.scripts.seed

.PHONY: dagster-materialize
dagster-materialize: ## Materialise all Dagster assets one-shot.
	$(COMPOSE) exec dagster-webserver dagster asset materialize \
	  --select '*' -m vindata_ingest.definitions

.PHONY: hindcast
hindcast: ## Run frost hindcast against fixture observations.
	$(COMPOSE) exec dagster-webserver python -m vindata_ingest.scripts.hindcast_frost

# -----------------------------------------------------------------------------
# Quality gates
# -----------------------------------------------------------------------------
.PHONY: lint
lint: ## Run all linters (ruff + eslint + prettier --check).
	uv run ruff check .
	pnpm -r --if-present lint

.PHONY: fmt
fmt: ## Format all code in place.
	uv run ruff format .
	uv run ruff check --fix .
	pnpm -r --if-present format

.PHONY: typecheck
typecheck: ## Type-check Python (mypy --strict) and TS (tsc --noEmit).
	uv run mypy apps/api/src packages/agronomy/src
	pnpm -r --if-present typecheck

.PHONY: test
test: test-agronomy test-api test-web ## Run all test suites.

.PHONY: test-agronomy
test-agronomy: ## Run agronomy package tests.
	uv run --package agronomy pytest packages/agronomy --cov=agronomy --cov-fail-under=90

.PHONY: test-api
test-api: ## Run API tests.
	uv run --package vindata-api pytest apps/api

.PHONY: test-web
test-web: ## Run web tests.
	pnpm --filter @vindata/web test --run

# -----------------------------------------------------------------------------
# Codegen
# -----------------------------------------------------------------------------
.PHONY: gen-types
gen-types: ## Regenerate the typed API client for apps/web from /openapi.json.
	@curl -fsS http://localhost:8000/openapi.json -o apps/api/openapi.json
	@pnpm --filter @vindata/web exec openapi-typescript ../../apps/api/openapi.json \
	  -o src/api/client.ts
	@echo "Regenerated apps/web/src/api/client.ts"

# -----------------------------------------------------------------------------
# E2E
# -----------------------------------------------------------------------------
.PHONY: smoke
smoke: ## Full end-to-end smoke from clean state.
	bash scripts/smoke.sh
