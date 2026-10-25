"""Проверка каталога построек и документального покрытия (пункт 21.14).

Запуск из корня репозитория: python3 docs/buildings/check-coverage.py
Возвращает ненулевой код, если покрытие неполно или обнаружены неверные ссылки/ресурсы.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import json
import yaml


DOCS = Path(__file__).resolve().parents[1]
ROOT = DOCS.parent
REGISTER = DOCS / "buildings/catalog-coverage.md"
BUILDINGS = ROOT / "shared/catalog/buildings.ts"
GENERATED = [ROOT / "shared/catalog/industrySpecs.generated.ts", ROOT / "shared/catalog/defenseSpecs.generated.ts"]
RESOURCES = ROOT / "shared/catalog/resources.ts"
BACKEND_IDS = ROOT / "backend/internal/domain/building/building.go"


def table_rows() -> list[list[str]]:
    result = []
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 7:
                result.append(cells)
    return result


def linked_path(cell: str, base: Path) -> Path | None:
    match = re.search(r"\]\(([^)#]+)(?:#[^)]+)?\)", cell)
    return (base / match.group(1)).resolve() if match else None


def main() -> int:
    errors: list[str] = []
    rows = table_rows()
    by_id: dict[str, list[str]] = {}
    for cells in rows:
        building_id = cells[0].strip("`")
        if building_id in by_id:
            errors.append(f"Повтор ID в реестре: {building_id}")
        by_id[building_id] = cells

    catalog = json.loads(subprocess.check_output(["node", str(DOCS / "buildings/export-shared-catalog.cjs")], text=True))
    by_catalog_id = {item["type"]: item for item in catalog["buildings"]}
    shared_ids = set(by_catalog_id)
    backend_ids = set(re.findall(r'Type\w+\s+Type\s*=\s*"([a-z][a-z0-9_]*)"', BACKEND_IDS.read_text(encoding="utf-8")))
    for name, ids in (("shared", shared_ids), ("backend", backend_ids)):
        for missing in sorted(ids - by_id.keys()):
            errors.append(f"{name}: нет текстовой строки для {missing}")
        for stale in sorted(by_id.keys() - ids):
            errors.append(f"{name}: лишняя строка {stale}")

    resource_ids = set(re.findall(r"\bid: '([^']+)'", RESOURCES.read_text(encoding="utf-8")))
    for source in [BUILDINGS, *GENERATED]:
        data = source.read_text(encoding="utf-8")
        for resource, amount in re.findall(r"resource:\s*'([^']+)',\s*amount:\s*(-?\d+)", data):
            if resource not in resource_ids:
                errors.append(f"{source.name}: неизвестный ресурс {resource}")
            if int(amount) < 0:
                errors.append(f"{source.name}: отрицательная стоимость {resource}={amount}")
    for building_id, cells in by_id.items():
        if not re.fullmatch(r"(?:\d+|\d+–\d+)", cells[2].replace(" ", "")):
            errors.append(f"{building_id}: неверный диапазон уровней {cells[2]}")
            expected = set()
        else:
            bounds = [int(part) for part in re.findall(r"\d+", cells[2])]
            expected = set(range(bounds[0], bounds[-1] + 1))
        catalog_item = by_catalog_id.get(building_id)
        if catalog_item:
            actual = catalog_item.get("upgradeLevels") or [catalog_item]
            catalog_levels = {level["level"] for level in actual}
            if expected != catalog_levels:
                errors.append(f"{building_id}: уровни реестра {sorted(expected)} != каталог {sorted(catalog_levels)}")
            for level in actual:
                for part in level["cost"]:
                    if part["resource"] not in resource_ids:
                        errors.append(f"{building_id} L{level['level']}: неизвестный ресурс {part['resource']}")
                    if part["amount"] < 0:
                        errors.append(f"{building_id} L{level['level']}: отрицательная цена {part['resource']}")
        text_path = linked_path(cells[3], REGISTER.parent)
        if text_path is None or not text_path.is_file():
            errors.append(f"{building_id}: отсутствует текстовая спека")
        visual_path = linked_path(cells[4], REGISTER.parent)
        if visual_path is None or not visual_path.is_file():
            errors.append(f"{building_id}: отсутствует визуальная спека или явное исключение")
        else:
            try:
                visual = json.loads(visual_path.read_text(encoding="utf-8")) if visual_path.suffix == ".json" else yaml.safe_load(visual_path.read_text(encoding="utf-8"))
            except (ValueError, yaml.YAMLError) as exc:
                errors.append(f"{building_id}: неверный формат визуальной спеки: {exc}")
                visual = None
            if isinstance(visual, dict):
                allowed_aliases = {"field_bed": "windleaf_bed", "road": "ground_road", "standard_road": "common_road"}
                if visual.get("asset_id") not in {building_id, allowed_aliases.get(building_id)}:
                    errors.append(f"{building_id}: asset_id={visual.get('asset_id')} не совпадает с игровым ID")
                level_numbers = [entry.get("level") for entry in visual.get("levels", []) if isinstance(entry, dict)]
                if expected and expected != set(level_numbers):
                    errors.append(f"{building_id}: уровни визуальной спеки {sorted(set(level_numbers))} != каталог {sorted(expected)}")
                for entry in visual.get("levels", []):
                    for resource in entry.get("cost_resources", []):
                        if resource not in resource_ids:
                            errors.append(f"{building_id}: неизвестный ресурс спеки {resource}")
                for reference in visual.get("references", {}).get("docs", []):
                    if not (ROOT / reference).is_file():
                        errors.append(f"{building_id}: отсутствует документ спеки {reference}")
        for cell in (cells[3], cells[4]):
            path = linked_path(cell, REGISTER.parent)
            if path is not None and not path.is_file():
                errors.append(f"{building_id}: битая ссылка {path.relative_to(ROOT)}")

    print(f"ID: {len(shared_ids)} shared / {len(backend_ids)} backend / {len(by_id)} docs")
    print(f"Ресурсы: {len(resource_ids)}; ошибок: {len(errors)}")
    for error in errors:
        print("FAIL", error)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
