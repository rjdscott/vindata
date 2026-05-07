#!/usr/bin/env bash
# scripts/smoke.sh — full Stage 00 end-to-end smoke from a clean state.
#
#   1. nuke + up
#   2. wait for healthchecks
#   3. apply migrations + seed
#   4. materialise the Dagster asset graph
#   5. assert the API returns ≥ 1 frost score for Cargo Road
#   6. print URLs to open in a browser

set -euo pipefail

cd "$(dirname "$0")/.."

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*" >&2; }

step() { printf "\n=== %s ===\n" "$1"; }

step "1/5 nuke + bring stack up"
make nuke >/dev/null 2>&1 || true
make up

step "2/5 apply migrations"
docker compose exec -T api alembic -c /app/apps/api/alembic.ini upgrade head

step "3/5 seed pilot vineyards"
docker compose exec -T api python -m vindata_api.scripts.seed

step "4/5 materialise Dagster asset graph"
docker compose exec -T dagster-webserver \
  dagster asset materialize --select '*' -m vindata_ingest.definitions

step "5/5 verify API returns frost scores for Cargo Road"
N=$(curl -fsS "http://localhost:8000/v1/vineyards/1/scores?wedge=frost&hours=72" \
      | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')
if [[ "$N" -lt 1 ]]; then
    red "FAIL: expected ≥1 frost score for vineyard 1, got $N"
    exit 1
fi

green "OK: $N frost scores for Cargo Road"
echo
echo "Open in your browser:"
echo "  Web:     http://localhost:5173"
echo "  API:     http://localhost:8000/docs"
echo "  Dagster: http://localhost:3001"
