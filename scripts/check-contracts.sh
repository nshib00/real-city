#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/player/generate_levels.py --check
python3 tools/buildings/check_balance_snapshot.py
cmp data/alliance/buffs.json backend/internal/domain/alliance/buffs.json
python3 tools/check_contracts.py
python3 docs/buildings/check-coverage.py
python3 docs/buildings/sync-runtime-tables.py --check
python3 docs/buildings/sync-xp-tables.py --check
(cd backend && go test ./internal/adapter/http ./internal/contract ./internal/domain/catalog ./internal/domain/player)
