#!/usr/bin/env bash
# Regenerate the Postman collection from the LIVE API's OpenAPI spec.
# FastAPI auto-generates /openapi.json from the route code, so the collection is always
# a faithful, current snapshot — re-run this whenever the API routes change.
#
# Requires: the stack running (`make up`) + node/npx. Override the API URL if needed:
#   API_URL=http://localhost:8011 bash scripts/gen_postman.sh
set -euo pipefail
cd "$(dirname "$0")/.."
API_URL="${API_URL:-http://localhost:8011}"

echo "[postman] fetching OpenAPI from ${API_URL}/openapi.json"
curl -fsS "${API_URL}/openapi.json" -o postman/openapi.json

echo "[postman] converting OpenAPI -> Postman v2.1 collection"
npx -y openapi-to-postmanv2 -s postman/openapi.json -o postman/HCIE.postman_collection.json -p

echo "[postman] done -> postman/HCIE.postman_collection.json"
echo "         Import that file into Postman (or 'Import > Link' the openapi.json for live sync)."
