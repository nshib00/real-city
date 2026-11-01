#!/usr/bin/env bash
# Снимок метрик API и PostgreSQL без изменения данных.
set -euo pipefail
compose=(docker compose -p real-city-test -f docker-compose.test.yml -f docker-compose.laptop.yml)
report=$(mktemp -d "${TMPDIR:-/tmp}/real-city-profile.XXXXXX")
echo "Профиль: $report"
curl --fail --silent --show-error http://127.0.0.1:18080/metrics > "$report/api-metrics.prom"
"${compose[@]}" exec -T postgres psql -X -U real_city -d real_city -v ON_ERROR_STOP=1 -c '
SELECT state, wait_event_type, wait_event, count(*) AS connections
FROM pg_stat_activity WHERE datname=current_database()
GROUP BY state, wait_event_type, wait_event ORDER BY connections DESC;
SELECT numbackends, xact_commit, xact_rollback, blks_read, blks_hit,
       tup_returned, tup_fetched, tup_inserted, tup_updated, tup_deleted,
       temp_files, deadlocks
FROM pg_stat_database WHERE datname=current_database();
SELECT relname, seq_scan, idx_scan, n_live_tup, n_dead_tup
FROM pg_stat_user_tables ORDER BY seq_scan DESC LIMIT 20;
' > "$report/postgres.txt"
"${compose[@]}" exec -T postgres psql -X -U real_city -d real_city -v ON_ERROR_STOP=1 -At -c \
  "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_stat_statements')" > "$report/pg-stat-statements-enabled.txt"
if [[ $(cat "$report/pg-stat-statements-enabled.txt") == t ]]; then
  "${compose[@]}" exec -T postgres psql -X -U real_city -d real_city -v ON_ERROR_STOP=1 -c '
  SELECT calls, round(total_exec_time::numeric,1) AS total_ms,
         round(mean_exec_time::numeric,1) AS mean_ms, rows,
         left(query, 200) AS query
  FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;
  ' > "$report/queries.txt"
fi
echo "Готово: $report"
