#!/usr/bin/env bash
# Task 5 — bit-identical parity gate. Brings up the ISOLATED test stack, runs the
# deterministic brain harness TWICE in fresh processes, compares the md5.
# Identical md5 == bit-identical replay across cross-session runs.
set -uo pipefail
cd "$(dirname "$0")/.."
COMPOSE="HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.test.yml"
HARNESS="research_validation/scripts/_determinism_parity.py"

echo "[parity] up isolated stack"
docker compose -f "$COMPOSE" up -d >/dev/null 2>&1
for i in $(seq 1 20); do docker exec hcie-test-pg pg_isready -U hcie_user >/dev/null 2>&1 && break; sleep 2; done
echo "[parity] copy live schema (schema-only) into test pg"
docker exec hcie-final-postgres pg_dump -U hcie_user -d hcie --schema-only --no-owner --no-privileges 2>/dev/null \
  | docker exec -i hcie-test-pg psql -U hcie_user -d hcie -q >/dev/null 2>&1

run_once () {
  MSYS_NO_PATHCONV=1 docker run --rm -i --network hcie-final-net \
    -e ENVIRONMENT=docker -e DOCKER_ENV=true \
    -e POSTGRES_HOST=hcie-test-pg -e POSTGRES_PORT=5432 -e POSTGRES_DB=hcie \
    -e POSTGRES_USER=hcie_user -e POSTGRES_PASSWORD=hcie_password \
    -e DATABASE_URL=postgresql://hcie_user:hcie_password@hcie-test-pg:5432/hcie \
    -e REDIS_HOST=hcie-test-redis -e REDIS_PORT=6379 \
    -e KAFKA_BOOTSTRAP_SERVERS=hcie-test-kafka:9092 \
    -e HCIE_FINALS_RUN_PG=1 -e HCIE_FINALS_RUN_REDIS=1 -e HCIE_FINALS_RUN_KAFKA=1 \
    -e ENABLE_DETERMINISTIC_MODE=true -e DETERMINISTIC_SEED=42 -e PYTHONHASHSEED=0 \
    01_compose-api python - < "$HARNESS" 2>/dev/null
}

echo "[parity] RUN 1"; OUT1="$(run_once)"
echo "[parity] RUN 2"; OUT2="$(run_once)"
MD51="$(echo "$OUT1" | python -c 'import sys,json;print(json.load(sys.stdin).get("md5","ERR1"))' 2>/dev/null)"
MD52="$(echo "$OUT2" | python -c 'import sys,json;print(json.load(sys.stdin).get("md5","ERR2"))' 2>/dev/null)"
echo "[parity] md5 run1 = $MD51"
echo "[parity] md5 run2 = $MD52"
if [ -n "$MD51" ] && [ "$MD51" = "$MD52" ]; then
  echo "[parity] RESULT: BIT-IDENTICAL ✓"
else
  echo "[parity] RESULT: DIFFERS ✗ (deterministic mode not yet bit-identical; see snapshots)"
  echo "$OUT1" > _parity_run1.json; echo "$OUT2" > _parity_run2.json
fi
echo "[parity] tearing down isolated stack"
docker compose -f "$COMPOSE" down >/dev/null 2>&1
