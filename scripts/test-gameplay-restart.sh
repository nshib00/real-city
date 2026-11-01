#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
checkpoint_dir=$(mktemp -d /tmp/real-city-restart.XXXXXX)
trap 'rm -rf "$checkpoint_dir"' EXIT
export REAL_CITY_API_URL="${REAL_CITY_API_URL:-http://127.0.0.1:18080}"
make test-backend-up
python3 tests/e2e/api/gameplay_restart.py --prepare "$checkpoint_dir/state.json"
# Restart processes only; keep the dedicated test database and its volumes.
docker compose -p real-city-test -f docker-compose.test.yml restart backend
python3 tests/e2e/api/gameplay_restart.py --verify "$checkpoint_dir/state.json"
