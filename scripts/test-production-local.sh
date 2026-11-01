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
stage=build
status=failed
: > "$artifact_dir/stages.jsonl"
mark_stage() {
  printf '{"stage":"%s","status":"passed"}\n' "$stage" >> "$artifact_dir/stages.jsonl"
}
export COMPOSE_PROJECT_NAME="real-city-acceptance-$(date +%s)-$$"
export POSTGRES_PASSWORD SESSION_SECRET
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
export DOMAIN=localhost BACKEND_IMAGE="real-city-backend:acceptance-$$" FRONTEND_IMAGE="real-city-frontend:acceptance-$$"
compose=(docker compose -f docker-compose.production.yml)
cleanup() {
  result=$?
  "${compose[@]}" unpause postgres >/dev/null 2>&1 || true
  "${compose[@]}" logs --no-color > "$artifact_dir/compose.log" 2>&1 || true
  "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  printf '{"status":"%s","last_stage":"%s","exit_code":%d,"rollback":"%s"}\n' "$status" "$stage" "$result" "$([[ "$skip_rollback" == 1 ]] && echo skipped || echo required)" > "$artifact_dir/result.json"
  rm -rf "$test_dir"
}
trap cleanup EXIT
docker build -t "$BACKEND_IMAGE" backend
docker build -f frontend/Dockerfile -t "$FRONTEND_IMAGE" .
mark_stage
stage=boot
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
mark_stage
stage=proxy
python3 - <<'PY'
import http.client
import urllib.error
import urllib.request

connection = http.client.HTTPConnection('localhost', 80, timeout=5)
connection.request('GET', '/client/redirect-check')
response = connection.getresponse()
assert response.status in (301, 308), f'HTTP redirect status: {response.status}'
assert response.getheader('Location') == 'https://localhost/client/redirect-check'
response.read()
connection.close()

with urllib.request.urlopen('https://localhost/') as response:
    headers = response.headers
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert headers['X-Frame-Options'] == 'DENY'
    assert headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert 'camera=()' in headers['Permissions-Policy']
for path in ('/metrics', '/debug/pprof'):
    try:
        urllib.request.urlopen('https://localhost' + path)
        raise AssertionError(f'{path} is public')
    except urllib.error.HTTPError as error:
        assert error.code == 404, f'{path}: {error.code}'

for origin, expected in (('https://localhost', 204), ('https://foreign.example', 403)):
    request = urllib.request.Request('https://localhost/api/v1/auth/login', method='OPTIONS',
        headers={'Origin': origin, 'Access-Control-Request-Method': 'POST'})
    try:
        with urllib.request.urlopen(request) as response:
            assert response.status == expected, f'CORS {origin}: {response.status}'
            assert response.headers['Access-Control-Allow-Origin'] == origin
    except urllib.error.HTTPError as error:
        assert error.code == expected, f'CORS {origin}: {error.code}'
        assert not error.headers.get('Access-Control-Allow-Origin')

request = urllib.request.Request('https://localhost/api/v1/auth/login',
    data=b'{"email":"' + b'x' * (1024 * 1024 + 1) + b'"}', method='POST',
    headers={'Content-Type': 'application/json'})
try:
    urllib.request.urlopen(request)
    raise AssertionError('oversized API body was accepted')
except urllib.error.HTTPError as error:
    assert error.code == 413, f'oversized API body: {error.code}'
print('PASS proxy redirect, security headers, CORS, internal routes and body limit')
PY
mark_stage
stage=frontend
curl --cacert "$SSL_CERT_FILE" -fsS https://localhost/ | python3 -c 'import sys; assert "<html" in sys.stdin.read()'
python3 - <<'PY'
import re
import urllib.request

base = 'https://localhost'
with urllib.request.urlopen(base + '/') as response:
    html = response.read().decode()
    assert response.status == 200
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
asset = re.search(r'src="(/assets/[^\"]+\.js)"', html)
assert asset, 'missing versioned JavaScript asset'
with urllib.request.urlopen(base + asset.group(1)) as response:
    assert response.status == 200
    assert 'immutable' in response.headers['Cache-Control']
with urllib.request.urlopen(base + '/client/unknown-route') as response:
    assert response.status == 200 and '<html' in response.read().decode()
print('PASS frontend asset cache headers and SPA fallback')
PY
mark_stage
stage=gameplay
python3 tests/e2e/api/gameplay_restart.py --prepare "$test_dir/state.json"
python3 tests/e2e/api/storage_outage.py before "$test_dir/outage.json"
export REAL_CITY_ACCESS_TOKEN
REAL_CITY_ACCESS_TOKEN=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["token"])' "$test_dir/outage.json")
python3 scripts/record-observability-baseline.py --base-url "$REAL_CITY_API_URL" --seconds 3 --workers 2 > "$artifact_dir/http.jsonl"
python3 scripts/measure-realtime.py --base-url "$REAL_CITY_API_URL" --seconds 4 --connections 8 > "$artifact_dir/ws.jsonl"
mark_stage
stage=storage_outage
"${compose[@]}" pause postgres
python3 - <<'PY'
import urllib.error
import urllib.request
import time
start = time.monotonic()
try:
    urllib.request.urlopen('https://localhost/ready', timeout=3)
    raise AssertionError('paused database reported ready')
except urllib.error.HTTPError as error:
    assert error.code == 503, f'readiness status: {error.code}'
assert time.monotonic() - start < 1.5, 'readiness exceeded 1.5 seconds'
print('PASS bounded readiness during paused database')
PY
python3 tests/e2e/api/storage_outage.py database-slow "$test_dir/outage.json"
"${compose[@]}" unpause postgres
python3 tests/e2e/api/storage_outage.py after "$test_dir/outage.json"
"${compose[@]}" stop redis
python3 tests/e2e/api/storage_outage.py after "$test_dir/outage.json"
"${compose[@]}" up -d --wait redis
"${compose[@]}" stop postgres
python3 tests/e2e/api/storage_outage.py database-down "$test_dir/outage.json"
"${compose[@]}" up -d --wait postgres
python3 tests/e2e/api/storage_outage.py after "$test_dir/outage.json"
mark_stage
stage=backup_restore
bash scripts/backup-production.sh "$test_dir/game.dump"
bash scripts/verify-production-backup.sh "$test_dir/game.dump"
mark_stage
stage=restart
"${compose[@]}" restart backend
python3 tests/e2e/api/gameplay_restart.py --verify "$test_dir/state.json"
mark_stage
stage=shutdown
backend_id=$("${compose[@]}" ps -q backend)
"${compose[@]}" stop -t 15 backend
backend_exit=$(docker inspect -f '{{.State.ExitCode}}' "$backend_id")
if [[ "$backend_exit" != 0 ]]; then
  echo "backend did not stop gracefully: exit $backend_exit" >&2
  exit 1
fi
"${compose[@]}" up -d --wait backend
curl --cacert "$SSL_CERT_FILE" -fsS https://localhost/ready >/dev/null
mark_stage
stage=rollback
if [[ "$skip_rollback" == 0 ]]; then
  bash scripts/test-production-rollback.sh "$test_dir/outage.json" "$artifact_dir/rollback.json"
else
  echo 'SKIPPED previous-release rollback: smoke only' >&2
  printf '{"status":"skipped","reason":"explicit smoke mode"}\n' > "$artifact_dir/rollback.json"
fi
if [[ "$skip_rollback" == 1 ]]; then
  printf '{"stage":"rollback","status":"skipped"}\n' >> "$artifact_dir/stages.jsonl"
else
  mark_stage
fi
stage=complete
status=passed
echo 'PASS production smoke: images, HTTPS, API/WS, restart, storage failures, backup and isolated restore'
