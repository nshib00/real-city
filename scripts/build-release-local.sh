#!/usr/bin/env bash
# Local images only; no registry login, push or deployment.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null
docker info >/dev/null
revision=$(git rev-parse HEAD)
if [[ -n $(git status --porcelain --untracked-files=normal) ]]; then
  echo 'Release build requires a clean working tree; commit reviewed changes first' >&2
  exit 2
fi
out=${REAL_CITY_RELEASE_ARTIFACTS:-artifacts/release}
mkdir -p "$out"
# Never leave the previous successful manifest in place after a failed build.
rm -f "$out/images.json"
docker build --label "org.opencontainers.image.revision=$revision" -t "real-city-backend:$revision" backend
docker build --label "org.opencontainers.image.revision=$revision" -f frontend/Dockerfile -t "real-city-frontend:$revision" .
backend_id=$(docker image inspect --format '{{.Id}}' "real-city-backend:$revision")
frontend_id=$(docker image inspect --format '{{.Id}}' "real-city-frontend:$revision")
python3 - "$out/images.json" "$revision" "$backend_id" "$frontend_id" <<'PY'
import json
import sys
from pathlib import Path
path, revision, backend, frontend = sys.argv[1:]
Path(path).write_text(json.dumps({
    'revision': revision,
    'backend': {'tag': f'real-city-backend:{revision}', 'image_id': backend},
    'frontend': {'tag': f'real-city-frontend:{revision}', 'image_id': frontend},
    'status': 'built-not-scanned-or-deployed',
    'identity': 'local image configuration digest; not a registry manifest digest',
}, indent=2) + '\n')
PY
echo "Local build manifest: $out/images.json (scan and rehearsal still required)"
