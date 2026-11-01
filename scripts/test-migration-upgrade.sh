#!/usr/bin/env bash
# Isolated schema in an explicitly configured disposable test database.
set -euo pipefail
cd "$(dirname "$0")/../backend"
: "${TEST_POSTGRES_DSN:?set TEST_POSTGRES_DSN to a disposable PostgreSQL database}"
command -v go >/dev/null
command -v psql >/dev/null
fixture_dir=$(mktemp -d)
schema="rc_upgrade_$(date +%s)_$$"
cleanup() {
  psql "$TEST_POSTGRES_DSN" -X -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS $schema CASCADE" >/dev/null
  rm -rf "$fixture_dir"
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
for migration in db/migrations/*.sql; do
  version=${migration##*/}
  if (( 10#${version%%_*} <= 48 )); then cp "$migration" "$fixture_dir/"; fi
done
MIGRATIONS_DIR="$fixture_dir" go run ./cmd/migrate up
psql "$POSTGRES_DSN" -X -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO players(id,email,name,password_hash) VALUES('upgrade_fixture','upgrade@example.invalid','UpgradeFixture','unused');
INSERT INTO player_profiles(player_id,display_name,xp) VALUES('upgrade_fixture','UpgradeFixture',3102);
INSERT INTO player_sessions(id,player_id,refresh_token_hash,expires_at) VALUES('upgrade_session','upgrade_fixture','unused_fixture_hash',now()+interval '1 day');
INSERT INTO player_xp_events(event_key,player_id,amount,requested_amount,reason,created_at) VALUES('upgrade_xp','upgrade_fixture',3102,3102,'upgrade_fixture',now());
SQL
snapshot() {
  psql "$POSTGRES_DSN" -X -At -v ON_ERROR_STOP=1 -c "SELECT row_to_json(p) FROM players p; SELECT row_to_json(p) FROM player_profiles p; SELECT row_to_json(s) FROM player_sessions s; SELECT row_to_json(e) FROM player_xp_events e; SELECT version,applied_at FROM schema_migrations WHERE version<=48 ORDER BY version;"
}
snapshot > "$fixture_dir/before"
go run ./cmd/migrate up
snapshot > "$fixture_dir/after"
cmp "$fixture_dir/before" "$fixture_dir/after"
psql "$POSTGRES_DSN" -X -At -v ON_ERROR_STOP=1 -c 'SELECT version,filename,applied_at FROM schema_migrations ORDER BY version' > "$fixture_dir/versions"
go run ./cmd/migrate up
psql "$POSTGRES_DSN" -X -At -v ON_ERROR_STOP=1 -c 'SELECT version,filename,applied_at FROM schema_migrations ORDER BY version' > "$fixture_dir/repeated"
cmp "$fixture_dir/versions" "$fixture_dir/repeated"
go run ./cmd/migrate status
psql "$POSTGRES_DSN" -X -v ON_ERROR_STOP=1 <<'SQL'
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version=50) THEN
    RAISE EXCEPTION 'migration 50 not applied';
  END IF;
END $$;
INSERT INTO player_pvp_losses(player_id,day,damage,destructions) VALUES('upgrade_fixture',date_trunc('day',now()),3102,1);
INSERT INTO account_admin_audit(id,actor_id,player_id,status,role,previous_status,previous_role,reason,created_at)
VALUES('upgrade_audit','upgrade_fixture','upgrade_fixture','active','user','active','user','Проверка миграций',now());
SQL
echo 'PASS schema 48 upgrade, preserved player/XP/session, repeated migrator, new PvP/audit tables'
