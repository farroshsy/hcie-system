#!/usr/bin/env bash
# Run the SonarQube scan on HCIE using the dockerized scanner (no local install needed).
# Prereqs:
#   docker compose -f HCIE_SYSTEM_BACKEND_FINAL/05_deployment/00_docker/01_compose/docker-compose.sonar.yml up -d
#   export SONAR_TOKEN=<token>   # SonarQube UI > My Account > Security, OR:
#     curl -s -u admin:admin -X POST "http://localhost:9000/api/user_tokens/generate?name=hcie-scan"
# Usage:   ./scripts/run_sonar_scan.sh
#
# IMPORTANT: do NOT edit files under 01_source while a scan is running — the scanner records
# line counts up-front and the server rejects the report if a file changes mid-scan
# ("Source of file ... has less lines than expected").
set -euo pipefail
cd "$(dirname "$0")/.."

: "${SONAR_TOKEN:?Set SONAR_TOKEN (see header for how to mint one)}"
SONAR_HOST="${SONAR_HOST:-http://host.docker.internal:9000}"

# Windows/Git-bash: pwd -W gives a Docker-acceptable path (D:/...); MSYS_NO_PATHCONV stops
# Git-bash from mangling the container-side /usr/src path. Both are no-ops on Linux/macOS.
HOSTDIR="$(pwd -W 2>/dev/null || pwd)"

echo "[sonar] scanning $HOSTDIR -> $SONAR_HOST"
MSYS_NO_PATHCONV=1 docker run --rm \
  -e SONAR_HOST_URL="$SONAR_HOST" \
  -e SONAR_TOKEN="$SONAR_TOKEN" \
  -v "$HOSTDIR:/usr/src" \
  --add-host=host.docker.internal:host-gateway \
  sonarsource/sonar-scanner-cli
echo "[sonar] done — open $SONAR_HOST/dashboard?id=hcie"
