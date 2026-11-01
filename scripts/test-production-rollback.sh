#!/usr/bin/env bash
# Only called inside the disposable production rehearsal project, after backup.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# != 2 || ! -f "$1" ]]; then
  echo 'Usage: test-production-rollback.sh checkpoint.json report.json' >&2
  exit 2
fi
if [[ ${COMPOSE_PROJECT_NAME:-} != real-city-acceptance-* ]]; then
  echo 'Rollback rehearsal requires an isolated real-city-acceptance-* project' >&2
  exit 2
fi
# A failed retry must not leave an old successful report in the artifact path.
printf '{"status":"running"}\n' > "$2"
report_path=$2
failed_report() {
  result=$?
  if (( result != 0 )); then
    printf '{"status":"failed","exit_code":%d}\n' "$result" > "$report_path"
  fi
}
trap failed_report EXIT
: "${BACKEND_IMAGE:?}" "${FRONTEND_IMAGE:?}" "${SSL_CERT_FILE:?}"
: "${REAL_CITY_PREVIOUS_BACKEND_IMAGE:?}" "${REAL_CITY_PREVIOUS_FRONTEND_IMAGE:?}"
current_backend=$BACKEND_IMAGE
current_frontend=$FRONTEND_IMAGE
compose=(docker compose -f docker-compose.production.yml)
for image in "$REAL_CITY_PREVIOUS_BACKEND_IMAGE" "$REAL_CITY_PREVIOUS_FRONTEND_IMAGE"; do
  docker image inspect "$image" >/dev/null 2>&1 || docker pull "$image"
done
current_backend_id=$(docker image inspect --format '{{.Id}}' "$current_backend")
current_frontend_id=$(docker image inspect --format '{{.Id}}' "$current_frontend")
previous_backend_id=$(docker image inspect --format '{{.Id}}' "$REAL_CITY_PREVIOUS_BACKEND_IMAGE")
previous_frontend_id=$(docker image inspect --format '{{.Id}}' "$REAL_CITY_PREVIOUS_FRONTEND_IMAGE")
if [[ "$current_backend_id" == "$previous_backend_id" && "$current_frontend_id" == "$previous_frontend_id" ]]; then
  echo 'Both release images are identical: retagging is not a rollback' >&2
  exit 2
fi
started=$(date +%s)
check_release() {
  curl --retry 10 --retry-delay 1 --retry-connrefused --cacert "$SSL_CERT_FILE" -fsS "$REAL_CITY_API_URL/ready" >/dev/null
  curl --cacert "$SSL_CERT_FILE" -fsS "$REAL_CITY_API_URL/" | python3 -c 'import sys; assert "<html" in sys.stdin.read()'
  # Same persisted account, session and inventory must survive each transition.
  python3 tests/e2e/api/storage_outage.py after "$1"
}
deploy() {
  # Do not run old and new simulations concurrently or roll migrations down.
  "${compose[@]}" stop backend web
  "${compose[@]}" up -d --wait backend web
  check_release "$1"
}
check_release "$1"
export BACKEND_IMAGE=$REAL_CITY_PREVIOUS_BACKEND_IMAGE FRONTEND_IMAGE=$REAL_CITY_PREVIOUS_FRONTEND_IMAGE
deploy "$1"
rollback_finished=$(date +%s)
export BACKEND_IMAGE=$current_backend FRONTEND_IMAGE=$current_frontend
deploy "$1"
python3 - "$2" "$started" "$rollback_finished" "$current_backend_id" "$current_frontend_id" "$previous_backend_id" "$previous_frontend_id" <<'PY'
import json
from pathlib import Path
import sys
import time
path, started, rolled_back, backend, frontend, old_backend, old_frontend = sys.argv[1:]
Path(path).write_text(json.dumps({
    'status': 'passed', 'mode': 'previous release on forward-migrated schema',
    'current': {'backend': backend, 'frontend': frontend},
    'previous': {'backend': old_backend, 'frontend': old_frontend},
    'rollback_seconds': int(rolled_back) - int(started),
    'roundtrip_seconds': int(time.time()) - int(started),
    'checks': ['HTTPS', 'readiness', 'frontend', 'persisted session', 'inventory', 'private WS'],
    'scope': 'compatible-schema rollback; backup restore tested separately',
}, ensure_ascii=False, indent=2) + '\n')
PY
echo 'PASS previous-release rollback and upgrade on the forward-migrated schema'
