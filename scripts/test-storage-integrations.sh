#!/usr/bin/env bash
# Run live repository tests in a disposable PostgreSQL schema.
set -euo pipefail
cd "$(dirname "$0")/../backend"
: "${TEST_POSTGRES_DSN:?set TEST_POSTGRES_DSN to a disposable PostgreSQL database}"
: "${TEST_REDIS_ADDR:?set TEST_REDIS_ADDR to a test Redis server}"
command -v go >/dev/null
command -v psql >/dev/null
command -v python3 >/dev/null
schema="rc_integration_$(date +%s)_$$"
cleanup() {
  psql "$TEST_POSTGRES_DSN" -X -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS $schema CASCADE" >/dev/null
}
trap cleanup EXIT
psql "$TEST_POSTGRES_DSN" -X -v ON_ERROR_STOP=1 -c "CREATE SCHEMA $schema" >/dev/null
export POSTGRES_DSN
POSTGRES_DSN=$(python3 - "$schema" <<'PY'
import os
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

url = urlsplit(os.environ['TEST_POSTGRES_DSN'])
if url.scheme not in ('postgres', 'postgresql'):
    raise SystemExit('TEST_POSTGRES_DSN must be a PostgreSQL URI')
query = [(key, value) for key, value in parse_qsl(url.query) if key != 'options']
query.append(('options', '-csearch_path=' + sys.argv[1]))
print(urlunsplit((url.scheme, url.netloc, url.path, urlencode(query), url.fragment)))
PY
)
go run ./cmd/migrate up
export TEST_POSTGRES_DSN="$POSTGRES_DSN"
go test -count=1 -v ./internal/adapter/postgres ./internal/adapter/redis
echo 'PASS isolated PostgreSQL and Redis integration tests'
