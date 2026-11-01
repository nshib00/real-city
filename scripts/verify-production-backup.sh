#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 1 || ! -f "$1" ]]; then
  echo 'Использование: bash scripts/verify-production-backup.sh /путь/к/копии.dump' >&2
  exit 2
fi
# Restore into an isolated disposable container, never into the running database.
restore_container=$(docker run -d --rm -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine)
trap 'docker rm -f "$restore_container" >/dev/null 2>&1 || true' EXIT
for attempt in {1..60}; do
  # The image starts a temporary Unix-socket server while initializing. Wait
  # for the final TCP listener so createdb cannot race with that server's exit.
  if docker exec "$restore_container" pg_isready -h 127.0.0.1 -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$restore_container" createdb -h 127.0.0.1 -U postgres restore_check
docker exec -i "$restore_container" pg_restore -h 127.0.0.1 -U postgres -d restore_check --no-owner --no-acl --exit-on-error < "$1"
docker exec "$restore_container" psql -h 127.0.0.1 -U postgres -d restore_check -v ON_ERROR_STOP=1 -c 'SELECT count(*) AS applied_migrations FROM schema_migrations; SELECT count(*) AS players FROM players; SELECT count(*) AS buildings FROM buildings;'
echo 'Копия успешно восстановлена в изолированную базу.'
