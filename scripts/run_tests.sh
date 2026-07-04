#!/usr/bin/env bash
# Run the HCIE test suite against an ISOLATED stack (never the live/sealed DB), in a backend
# container (so `core.*` resolves + the brain wires its real stores), with coverage.
#
#   ./scripts/run_tests.sh                       # default suites
#   ./scripts/run_tests.sh 02_tests/00_unit      # custom scope
#
# Flow: bring up test pg/redis/kafka -> copy live SCHEMA (no data) -> pytest+coverage in the
# api image with the repo mounted read-only -> copy coverage.xml out -> tear the stack down.
# Coverage is written under /tmp inside the container (the mount is read-only), then copied to
# ./coverage.xml at the repo root for the sonar scan.
set -uo pipefail
cd "$(dirname "$0")/.."
COMPOSE="HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.test.yml"
SCOPE="${*:-02_tests/00_unit 02_tests/01_integration 02_tests/02_behavioral}"
HOSTDIR="$(pwd -W 2>/dev/null || pwd)"

echo "[tests] up isolated stack"
docker compose -f "$COMPOSE" up -d
echo "[tests] waiting for postgres..."
for i in $(seq 1 20); do docker exec hcie-test-pg pg_isready -U hcie_user >/dev/null 2>&1 && break; sleep 2; done
echo "[tests] copy live schema (schema-only, no data) into test pg"
docker exec hcie-final-postgres pg_dump -U hcie_user -d hcie --schema-only --no-owner --no-privileges 2>/dev/null \
  | docker exec -i hcie-test-pg psql -U hcie_user -d hcie -q >/dev/null 2>&1

echo "[tests] run pytest + coverage in the api image"
MSYS_NO_PATHCONV=1 docker run --rm -i --network hcie-final-net \
  -e ENVIRONMENT=docker -e DOCKER_ENV=true \
  -e JWT_SECRET_KEY=ci-test-secret-not-for-production \
  -e POSTGRES_HOST=hcie-test-pg -e POSTGRES_PORT=5432 -e POSTGRES_DB=hcie \
  -e POSTGRES_USER=hcie_user -e POSTGRES_PASSWORD=hcie_password \
  -e DATABASE_URL=postgresql://hcie_user:hcie_password@hcie-test-pg:5432/hcie \
  -e REDIS_HOST=hcie-test-redis -e REDIS_PORT=6379 \
  -e KAFKA_BOOTSTRAP_SERVERS=hcie-test-kafka:9092 \
  -e HCIE_FINALS_RUN_PG=1 -e HCIE_FINALS_RUN_REDIS=1 -e HCIE_FINALS_RUN_KAFKA=1 \
  -e ENABLE_DETERMINISTIC_MODE=true -e DETERMINISTIC_SEED=42 \
  -e COVERAGE_FILE=/tmp/.coverage \
  -v "$HOSTDIR/HCIE_SYSTEM_BACKEND_FINAL:/app/HCIE_SYSTEM_BACKEND_FINAL:ro" \
  -v "$HOSTDIR/HCIE_SYSTEM_BACKEND_FINAL/01_source:/app/01_source:ro" \
  -v "$HOSTDIR/HCIE_SYSTEM_BACKEND_FINAL/11_build:/app/11_build:ro" \
  -v "$HOSTDIR:/out" \
  01_compose-api bash -lc "pip install -q pytest pytest-cov pytest-timeout httpx 2>/dev/null; \
    cd /app/HCIE_SYSTEM_BACKEND_FINAL && \
    python -m pytest $SCOPE --continue-on-collection-errors --timeout=90 --timeout-method=thread \
      -p no:cacheprovider --cov=core --cov=app --cov=storage --cov=messaging --cov=infrastructure \
      --cov=config --cov-report=xml:/tmp/cov.xml -q; rc=\$?; cp /tmp/cov.xml /out/coverage.xml 2>/dev/null; exit \$rc"
rc=$?

echo "[tests] rewrite in-container paths -> host paths so sonar can map coverage"
# the brain runs from /app/01_source (runtime projection); sonar scans HCIE_SYSTEM_BACKEND_FINAL/01_source
if [ -f coverage.xml ]; then
  sed -i 's#filename="/app/01_source/#filename="HCIE_SYSTEM_BACKEND_FINAL/01_source/#g' coverage.xml
fi
echo "[tests] tearing down isolated stack"
docker compose -f "$COMPOSE" down >/dev/null 2>&1
echo "[tests] coverage.xml at repo root (rc=$rc), paths rewritten for sonar."
exit $rc
