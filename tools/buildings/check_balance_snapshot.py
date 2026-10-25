"""Проверяет версионированный снимок баланса построек.

После изменения data/buildings/catalog-v2.json выполните
python3 tools/buildings/generate_catalog.py, затем эту проверку.
"""

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data/buildings/catalog-v2.json"


def main():
    current = json.loads(subprocess.check_output(["node", str(ROOT / "docs/buildings/export-shared-catalog.cjs")], text=True))
    saved = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if saved.get("schema_version") != 1 or saved.get("balance_version") != 2:
        raise SystemExit("неподдерживаемая версия снимка баланса")
    if (ROOT / "backend/internal/domain/catalog/buildings.v2.json").read_bytes() != SNAPSHOT.read_bytes():
        raise SystemExit("встроенный каталог Go устарел; запустите generate_catalog.py")
    known_resources = {resource["id"] for resource in current["resources"]}
    economy_source = (ROOT / "backend/internal/domain/economy/economy.go").read_text(encoding="utf-8")
    resource_source = (ROOT / "backend/internal/domain/catalog/economy.go").read_text(encoding="utf-8")
    constants = dict(re.findall(r'(Resource\w+)\s+ResourceType\s*=\s*"([^"]+)"', economy_source))
    resource_block = resource_source.split("var Resources = []ResourceSpec{", 1)[1].split("\n}", 1)[0]
    backend_resources = {constants[name] for name in re.findall(r"\{Type:\s*economy\.(Resource\w+)", resource_block)}
    if backend_resources != known_resources:
        raise SystemExit(f"ресурсные каталоги различаются: backend-only={sorted(backend_resources - known_resources)}, shared-only={sorted(known_resources - backend_resources)}")
    ids = set()
    for item in saved["buildings"]:
        building_id = item["type"]
        if building_id in ids:
            raise SystemExit(f"повтор building_id: {building_id}")
        ids.add(building_id)
        if not item["name"] or not item["category"] or item.get("health", 0) <= 0:
            raise SystemExit(f"нет имени или категории: {building_id}")
        if item["footprint"]["width"] < 1 or item["footprint"]["height"] < 1:
            raise SystemExit(f"неверный размер: {building_id}")
        levels = item.get("upgradeLevels") or [item]
        if len({level["level"] for level in levels}) != len(levels):
            raise SystemExit(f"повтор уровня: {building_id}")
        for level in levels:
            if level["buildSeconds"] < 0 or level["population"] < 0 or level.get("health", 0) <= 0:
                raise SystemExit(f"отрицательная характеристика: {building_id} L{level['level']}")
            for cost in level["cost"]:
                if cost["amount"] < 0 or cost["resource"] not in known_resources:
                    raise SystemExit(f"неверная цена: {building_id} L{level['level']}: {cost}")
    if saved["buildings"] != current["buildings"]:
        raise SystemExit("shared-каталог не совпадает с data; запустите generate_catalog.py")
    print(f"каталог data v2: {len(ids)} построек и {len(known_resources)} ресурсов; shared и Go совпадают")


if __name__ == "__main__":
    main()
