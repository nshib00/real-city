#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test_dir=$(mktemp -d)
api_pid=''
cleanup() { if [[ -n "$api_pid" ]]; then kill "$api_pid" 2>/dev/null || true; wait "$api_pid" 2>/dev/null || true; fi; rm -rf "$test_dir"; }
trap cleanup EXIT
export SERVER_ADDR="${SERVER_ADDR:-127.0.0.1:18080}"
export REAL_CITY_API_URL="${REAL_CITY_API_URL:-http://127.0.0.1:18080}"
export SIMULATION_EMBEDDED=true
(cd backend && go build -o "$test_dir/api" ./cmd/api)
(cd backend && exec "$test_dir/api") >"$test_dir/api.log" 2>&1 &
api_pid=$!
if ! python3 tests/e2e/api/gameplay_restart.py --prepare "$test_dir/state.json"; then cat "$test_dir/api.log"; exit 1; fi
kill "$api_pid"; wait "$api_pid" || true; api_pid=''
(cd backend && exec "$test_dir/api") >>"$test_dir/api.log" 2>&1 &
api_pid=$!
if ! python3 tests/e2e/api/gameplay_restart.py --verify "$test_dir/state.json"; then cat "$test_dir/api.log"; exit 1; fi
