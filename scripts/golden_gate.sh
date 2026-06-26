#!/usr/bin/env bash
# Golden-master gate for refactoring unified_brain (e.g. the _write_mode split).
# Runs the deterministic brain harness against the LIVE HOST source (mounted over the baked
# image) so uncommitted edits are exercised, and prints the snapshot JSON to stdout.
# Usage:
#   bash scripts/golden_gate.sh > before.json      # capture baseline (pre-refactor)
#   <edit unified_brain.py>
#   bash scripts/golden_gate.sh > after.json
#   diff before.json after.json                    # MUST be empty == bit-identical == safe
# Leaves the isolated test stack running for repeated calls; tear down with:
#   docker compose -f HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.test.yml down
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
BE="$ROOT/HCIE_SYSTEM_BACKEND_FINAL"
COMPOSE="$BE/05_deployment/00_docker/01_compose/docker-compose.test.yml"

if ! docker ps --format '{{.Names}}' | grep -q hcie-test-pg; then
  echo "[golden] bringing up isolated test stack" >&2
  docker compose -f "$COMPOSE" up -d >/dev/null 2>&1
  for i in $(seq 1 20); do docker exec hcie-test-pg pg_isready -U hcie_user >/dev/null 2>&1 && break; sleep 2; done
  echo "[golden] copying live schema (schema-only) into test pg" >&2
  docker exec hcie-final-postgres pg_dump -U hcie_user -d hcie --schema-only --no-owner --no-privileges 2>/dev/null \
    | docker exec -i hcie-test-pg psql -U hcie_user -d hcie -q >/dev/null 2>&1
fi

MSYS_NO_PATHCONV=1 docker run --rm -i --network hcie-final-net \
  -v "$BE/01_source:/app/01_source:ro" \
  -v "$BE/11_build:/app/11_build:ro" \
  -e ENVIRONMENT=docker -e DOCKER_ENV=true \
  -e POSTGRES_HOST=hcie-test-pg -e POSTGRES_PORT=5432 -e POSTGRES_DB=hcie \
  -e POSTGRES_USER=hcie_user -e POSTGRES_PASSWORD=hcie_password \
  -e DATABASE_URL=postgresql://hcie_user:hcie_password@hcie-test-pg:5432/hcie \
  -e REDIS_HOST=hcie-test-redis -e REDIS_PORT=6379 \
  -e KAFKA_BOOTSTRAP_SERVERS=hcie-test-kafka:9092 \
  -e HCIE_FINALS_RUN_PG=1 -e HCIE_FINALS_RUN_REDIS=1 -e HCIE_FINALS_RUN_KAFKA=1 \
  -e ENABLE_DETERMINISTIC_MODE=true -e DETERMINISTIC_SEED=42 -e PYTHONHASHSEED=0 \
  01_compose-api python - < scripts/brain_golden_master.py 2>/dev/null
