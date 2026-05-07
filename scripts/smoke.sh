#!/usr/bin/env bash
# scripts/smoke.sh — full Stage 00 end-to-end smoke from a clean state.
#
#   1. nuke + up
#   2. wait for healthchecks
#   3. apply migrations + seed
#   4. materialise the Dagster asset graph
#   5. assert the API returns >=1 row for every wedge on Cargo Road
#   6. print URLs to open in a browser

set -euo pipefail

cd "$(dirname "$0")/.."

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*" >&2; }
yellow(){ printf "\033[33m%s\033[0m\n" "$*"; }

step() { printf "\n=== %s ===\n" "$1"; }

step "1/6 nuke + bring stack up"
make nuke >/dev/null 2>&1 || true
make up

step "2/6 apply migrations"
docker compose exec -T api alembic -c /app/apps/api/alembic.ini upgrade head

step "3/6 seed pilot vineyards"
docker compose exec -T api python -m vindata_api.scripts.seed

step "4/6 materialise Dagster asset graph"
docker compose exec -T dagster-webserver \
  dagster asset materialize --select '*' -m vindata_ingest.definitions

step "5/6 verify API returns rows for every wedge on Cargo Road"
count_wedge() {
    local wedge="$1"
    local hours="$2"
    curl -fsS "http://localhost:8000/v1/vineyards/1/scores?wedge=${wedge}&hours=${hours}" \
      | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))'
}

declare -A REQUIRED=(
    [frost]=72
    [dm]=168
)
# Other wedges are best-effort: PM/Botrytis are gated on BBCH >= 53 (which
# only fires once flowering has been reached for the seeded blocks), and
# smoke depends on NSW EPA returning data for Bathurst. We assert >=1
# row only for the wedges we can guarantee in a fresh smoke run.

for wedge in "${!REQUIRED[@]}"; do
    n=$(count_wedge "$wedge" "${REQUIRED[$wedge]}")
    if [[ "$n" -lt 1 ]]; then
        red "FAIL: expected >=1 ${wedge} score for vineyard 1, got $n"
        exit 1
    fi
    green "OK: $n ${wedge} scores"
done

# Phenology has its own endpoint keyed by block_id (Cargo Road has block 1).
n_pheno=$(curl -fsS "http://localhost:8000/v1/blocks/1/phenology?days=200" \
            | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')
if [[ "$n_pheno" -lt 1 ]]; then
    red "FAIL: expected >=1 phenology row for block 1, got $n_pheno"
    exit 1
fi
green "OK: $n_pheno phenology rows"

step "6/6 best-effort wedge counts (PM / Botrytis / Smoke)"
for wedge in pm botrytis smoke; do
    n=$(count_wedge "$wedge" 168 || echo 0)
    if [[ "$n" -lt 1 ]]; then
        yellow "INFO: $wedge has 0 rows (BBCH gate / external API offline) — non-blocking"
    else
        green "OK: $n ${wedge} scores"
    fi
done

echo
echo "Open in your browser:"
echo "  Web:     http://localhost:5173"
echo "  API:     http://localhost:8000/docs"
echo "  Dagster: http://localhost:3001"
