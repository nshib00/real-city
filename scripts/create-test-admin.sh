#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8080/api/v1}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_NAME="${ADMIN_NAME:-Test Admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin12345}"

payload=$(printf '{"email":"%s","name":"%s","password":"%s"}' "$ADMIN_EMAIL" "$ADMIN_NAME" "$ADMIN_PASSWORD")
body_file="$(mktemp)"
status_file="$(mktemp)"
trap 'rm -f "$body_file" "$status_file"' EXIT

curl -sS -o "$body_file" -w "%{http_code}" \
  -X POST "$API_URL/auth/register" \
  -H 'Content-Type: application/json' \
  -d "$payload" >"$status_file"
status="$(cat "$status_file")"

case "$status" in
  201)
    echo "Created test user: $ADMIN_EMAIL"
    ;;
  409)
    login_payload=$(printf '{"email":"%s","password":"%s"}' "$ADMIN_EMAIL" "$ADMIN_PASSWORD")
    curl -sS -o "$body_file" -w "%{http_code}" \
      -X POST "$API_URL/auth/login" \
      -H 'Content-Type: application/json' \
      -d "$login_payload" >"$status_file"
    login_status="$(cat "$status_file")"
    if [ "$login_status" != "200" ]; then
      echo "User exists, but login with ADMIN_PASSWORD failed. HTTP $login_status" >&2
      cat "$body_file" >&2
      exit 1
    fi
    echo "Test user already exists and credentials are valid: $ADMIN_EMAIL"
    ;;
  *)
    echo "Registration failed. HTTP $status" >&2
    cat "$body_file" >&2
    exit 1
    ;;
esac

promote_sql="UPDATE players SET role = 'admin', updated_at = now() WHERE email = :'admin_email';"

if [ -n "${POSTGRES_DSN:-}" ] && command -v psql >/dev/null 2>&1; then
  psql "$POSTGRES_DSN" -v ON_ERROR_STOP=1 -v admin_email="$ADMIN_EMAIL" \
    -c "$promote_sql" >/dev/null
  echo "Promoted test user to admin in Postgres: $ADMIN_EMAIL"
elif command -v docker >/dev/null 2>&1; then
  docker compose exec -T postgres psql -U real_city -d real_city -v ON_ERROR_STOP=1 -v admin_email="$ADMIN_EMAIL" \
    -c "$promote_sql" >/dev/null
  echo "Promoted test user to admin in Docker Postgres: $ADMIN_EMAIL"
else
  echo "Admin promotion skipped: set POSTGRES_DSN and install psql, or run Docker Postgres."
fi

echo "Credentials: $ADMIN_EMAIL / $ADMIN_PASSWORD"
