#!/usr/bin/env bash
# Generate coverage.xml for the SonarQube scan.
#
#   ./scripts/run_coverage.sh                       # host-runnable unit tests (default)
#   ./scripts/run_coverage.sh <pytest-path>         # custom scope
#
# Then run ./scripts/run_sonar_scan.sh to publish coverage to the dashboard.
#
# NOTE on the number: only the UNIT tests run cleanly on the host. The integration /
# behavioral / research suites exercise most of 01_source (incl. unified_brain) but need
# the running stack (postgres/redis/kafka via docker hostnames), so for a HIGH coverage
# number run pytest INSIDE the api container instead (it has the runtime + network).
# Requires: pip install pytest pytest-cov  (already in requirements-compliance.txt).
set -uo pipefail
cd "$(dirname "$0")/.."
SCOPE="${1:-HCIE_SYSTEM_BACKEND_FINAL/02_tests/00_unit}"

echo "[coverage] running pytest on: $SCOPE"
python3 -m pytest "$SCOPE" \
  -c HCIE_SYSTEM_BACKEND_FINAL/pytest.ini \
  --continue-on-collection-errors \
  --cov=HCIE_SYSTEM_BACKEND_FINAL/01_source \
  --cov-report=xml:coverage.xml -q -p no:cacheprovider || true

# Rewrite the absolute <source> to a relative path so the dockerized sonar-scanner
# (project base = /usr/src) can resolve coverage filenames against sonar.sources.
python3 - <<'PY'
import re, os
p = "coverage.xml"
if not os.path.exists(p):
    raise SystemExit("[coverage] ERROR: coverage.xml not produced")
s = open(p, encoding="utf-8").read()
s = re.sub(r"<source>.*?</source>",
          "<source>HCIE_SYSTEM_BACKEND_FINAL/01_source</source>", s, count=1, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
m = re.search(r'line-rate="([0-9.]+)"', s)
print(f"[coverage] coverage.xml ready (scanner-relative source); line-rate "
      f"{round(float(m.group(1))*100,1) if m else '?'}%")
PY
