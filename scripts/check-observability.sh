#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

python3 - <<'PY'
import json
from pathlib import Path

directory = Path("deploy/observability/grafana/dashboards")
files = sorted(directory.glob("*.json"))
assert files, "No Grafana dashboards"
uids = set()
expressions = []
for path in files:
    dashboard = json.loads(path.read_text(encoding="utf-8"))
    uid = dashboard.get("uid")
    assert uid and uid not in uids, f"Missing or duplicate dashboard UID: {path}"
    uids.add(uid)
    panels = dashboard.get("panels", [])
    assert panels, f"Dashboard without panels: {path}"
    for panel in panels:
        for target in panel.get("targets", []):
            expression = target.get("expr", "").strip()
            if expression:
                expressions.append(expression)
assert expressions, "No PromQL expressions in dashboards"
rules = {"groups": [{"name": "dashboard-syntax", "rules": [
    {"record": f"real_city_dashboard_syntax_{i}", "expr": expr}
    for i, expr in enumerate(expressions)
]}]}
output = Path("/tmp/real-city-dashboard-promql-rules.yml")
lines = ["groups:", "  - name: dashboard-syntax", "    rules:"]
for rule in rules["groups"][0]["rules"]:
    lines += [f"      - record: {rule['record']}", f"        expr: {json.dumps(rule['expr'])}"]
output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Grafana: {len(files)} dashboards, {len(expressions)} PromQL queries")
PY

docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.observability.yml config --quiet

if command -v promtool >/dev/null 2>&1; then
  promtool check config deploy/observability/prometheus/prometheus.yml
  promtool check rules deploy/observability/prometheus/alerts.yml /tmp/real-city-dashboard-promql-rules.yml
else
  docker run --rm --entrypoint /bin/promtool \
    -v "$root_dir/deploy/observability/prometheus:/etc/prometheus:ro" \
    -v /tmp/real-city-dashboard-promql-rules.yml:/tmp/dashboard-rules.yml:ro \
    prom/prometheus:v3.15.0 check config /etc/prometheus/prometheus.yml
  docker run --rm --entrypoint /bin/promtool \
    -v "$root_dir/deploy/observability/prometheus:/etc/prometheus:ro" \
    -v /tmp/real-city-dashboard-promql-rules.yml:/tmp/dashboard-rules.yml:ro \
    prom/prometheus:v3.15.0 check rules /etc/prometheus/alerts.yml /tmp/dashboard-rules.yml
fi
