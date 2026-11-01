#!/usr/bin/env bash
# Только чтение. Запускать из терминала хоста; не собирает env и аргументы процессов.
set -euo pipefail
duration=${1:-60}
if ! [[ "$duration" =~ ^[0-9]+$ ]] || ((duration < 2 || duration > 3600)); then
  echo 'Продолжительность должна быть от 2 до 3600 секунд' >&2
  exit 2
fi
docker info --format '{{.ServerVersion}}' >/dev/null
report=$(mktemp -d "${TMPDIR:-/tmp}/real-city-resources.XXXXXX")
echo "Отчёт: $report"
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' > "$report/containers.txt"
ps -eo pid,ppid,comm,pcpu,pmem,rss --sort=-pcpu > "$report/processes-before.txt"
free -m > "$report/memory-before.txt"
vmstat 1 "$((duration + 1))" > "$report/vmstat.txt" &
vmstat_pid=$!
trap 'kill "$vmstat_pid" 2>/dev/null || true' EXIT
# Потоковый замер, первая строка каждого контейнера может быть разогревочной.
timeout --signal=TERM "${duration}s" docker stats --format '{{json .}}' | python3 -c '
import json, sys
decoder = json.JSONDecoder()
for line in sys.stdin:
    start = line.find("{")
    if start >= 0:
        try:
            item, _ = decoder.raw_decode(line[start:])
            print(json.dumps(item, ensure_ascii=False), flush=True)
        except json.JSONDecodeError:
            pass
' > "$report/docker-stats.jsonl" || {
  status=$?
  if ((status != 124)); then exit "$status"; fi
}
wait "$vmstat_pid"
trap - EXIT
ps -eo pid,ppid,comm,pcpu,pmem,rss --sort=-pcpu > "$report/processes-after.txt"
free -m > "$report/memory-after.txt"
echo "Готово: $report (первую строку данных vmstat исключить из сравнения)"
