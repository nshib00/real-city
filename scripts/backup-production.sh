#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# != 1 ]]; then
  echo 'Использование: bash scripts/backup-production.sh /путь/к/новой-копии.dump' >&2
  exit 2
fi
umask 077
backup_path=$1
if [[ -e "$backup_path" ]]; then echo 'Файл уже существует' >&2; exit 2; fi
partial_path=$(mktemp "${backup_path}.partial.XXXXXX")
trap 'rm -f "$partial_path"' EXIT
docker compose -f docker-compose.production.yml exec -T postgres pg_dump -U real_city -d real_city --format=custom > "$partial_path"
docker compose -f docker-compose.production.yml exec -T postgres pg_restore --list < "$partial_path" > /dev/null
# Hard-link publishes only a complete dump and cannot overwrite an existing backup.
ln "$partial_path" "$backup_path"
echo "Резервная копия: $backup_path"
