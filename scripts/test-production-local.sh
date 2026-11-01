#!/usr/bin/env bash
# Isolated production rehearsal; never attaches to production volumes.
set -euo pipefail
cd "$(dirname "$0")/.."
# Full acceptance requires actual previous release images. PR smoke may explicitly
# skip this stage, but must never report successful rollback acceptance.
skip_rollback=${REAL_CITY_SKIP_ROLLBACK:-0}
if [[ "$skip_rollback" != 0 && "$skip_rollback" != 1 ]]; then
  echo 'REAL_CITY_SKIP_ROLLBACK must be 0 or 1' >&2
  exit 2
fi
if [[ "$skip_rollback" == 0 ]]; then
  : "${REAL_CITY_PREVIOUS_BACKEND_IMAGE:?set previous release backend image}"
  : "${REAL_CITY_PREVIOUS_FRONTEND_IMAGE:?set previous release frontend image}"
fi
test_dir=$(mktemp -d)
artifact_dir=${REAL_CITY_ACCEPTANCE_ARTIFACTS:-$(mktemp -d /tmp/real-city-acceptance-reports.XXXXXX)}
mkdir -p "$artifact_dir"
echo "Acceptance reports: $artifact_dir"
export COMPOSE_PROJECT_NAME="real-city-acceptance-$(date +%s)-$$"
export POSTGRES_PASSWORD SESSION_SECRET
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
export DOMAIN=localhost BACKEND_IMAGE="real-city-backend:acceptance-$$" FRONTEND_IMAGE="real-city-frontend:acceptance-$$"
compose=(docker compose -f docker-compose.production.yml)
cleanup() {
  "${compose[@]}" unpause postgres >/dev/null 2>&1 || true
  "${compose[@]}" logs --no-color > "$artifact_dir/compose.log" 2>&1 || true
  "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$test_dir"
}
trap cleanup EXIT
docker build -t "$BACKEND_IMAGE" backend
docker build -f frontend/Dockerfile -t "$FRONTEND_IMAGE" .
"${compose[@]}" up -d --wait postgres redis
"${compose[@]}" run --rm backend /app/migrate up
"${compose[@]}" run --rm backend /app/migrate up
"${compose[@]}" up -d --wait
for attempt in {1..60}; do
  if curl -kfsS https://localhost/ready >/dev/null; then break; fi
  sleep 1
done
web_id=$("${compose[@]}" ps -q web)
docker cp "$web_id:/data/caddy/pki/authorities/local/root.crt" "$test_dir/ca.crt" >/dev/null
export SSL_CERT_FILE="$test_dir/ca.crt" REAL_CITY_API_URL=https://localhost
curl --cacert "$SSL_CERT_FILE" -fsS https://localhost/ready >/dev/null
curl --cacert "$SSL_CERT_FILE" -fsS https://localhost/ | python3 -c 'import sys; assert "<html" in sys.stdin.read()'
python3 tests/e2e/api/gameplay_restart.py --prepare "$test_dir/state.json"
python3 tests/e2e/api/storage_outage.py before "$test_dir/outage.json"
export REAL_CITY_ACCESS_TOKEN
REAL_CITY_ACCESS_TOKEN=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["token"])' "$test_dir/outage.json")
python3 scripts/record-observability-baseline.py --base-url "$REAL_CITY_API_URL" --seconds 3 --workers 2 > "$artifact_dir/http.jsonl"
python3 scripts/measure-realtime.py --base-url "$REAL_CITY_API_URL" --seconds 4 --connections 8 > "$artifact_dir/ws.jsonl"
"${compose[@]}" pause postgres
python3 tests/e2e/api/storage_outage.py database-down "$test_dir/outage.json"
"${compose[@]}" unpause postgres
python3 tests/e2e/api/storage_outage.py after "$test_dir/outage.json"
"${compose[@]}" stop redis
python3 tests/e2e/api/storage_outage.py after "$test_dir/outage.json"
"${compose[@]}" up -d --wait redis
"${compose[@]}" stop postgres
python3 tests/e2e/api/storage_outage.py database-down "$test_dir/outage.json"
"${compose[@]}" up -d --wait postgres
python3 tests/e2e/api/storage_outage.py after "$test_dir/outage.json"
bash scripts/backup-production.sh "$test_dir/game.dump"
bash scripts/verify-production-backup.sh "$test_dir/game.dump"
"${compose[@]}" restart backend
python3 tests/e2e/api/gameplay_restart.py --verify "$test_dir/state.json"
if [[ "$skip_rollback" == 0 ]]; then
  bash scripts/test-production-rollback.sh "$test_dir/outage.json" "$artifact_dir/rollback.json"
else
  echo 'SKIPPED previous-release rollback: smoke only' >&2
  printf '{"status":"skipped","reason":"explicit smoke mode"}\n' > "$artifact_dir/rollback.json"
fi
echo 'PASS production smoke: images, HTTPS, API/WS, restart, storage failures, backup and isolated restore'
