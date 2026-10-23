#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The test Compose project exposes its own Postgres on port 15432.
export APP_ENV=test
export POSTGRES_DSN='postgres://real_city:real_city@127.0.0.1:15432/real_city?sslmode=disable'

cd "$repo_root/backend"
go run ./cmd/test-admin
