#!/usr/bin/env bash
# Full gate fails closed when a required tool is absent. frontend mode is explicitly partial.
set -euo pipefail
cd "$(dirname "$0")/.."
mode=${1:-full}
if [[ "$mode" != full && "$mode" != frontend ]]; then
  echo 'Usage: bash scripts/check-quality.sh [full|frontend]' >&2
  exit 2
fi
node --version
npm --version
if [[ "$mode" == full ]]; then
  if ! command -v go >/dev/null; then
    echo 'Full quality gate requires a real Go toolchain on PATH' >&2
    exit 1
  fi
  go version
  unformatted=$(gofmt -l backend)
  if [[ -n "$unformatted" ]]; then
    echo "$unformatted" >&2
    echo 'Go formatting check failed' >&2
    exit 1
  fi
  (cd backend && go vet ./... && go test -race ./... && go build ./cmd/...)
  bash scripts/check-contracts.sh
fi
(cd frontend && npm run lint && npm test && npm run build)
echo "PASS quality mode=$mode"
