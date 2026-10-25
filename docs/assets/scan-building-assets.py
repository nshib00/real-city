"""Обновляет реестр 22.1 по фактическим файлам, не меняя игровые каталоги."""

from __future__ import annotations

import json
import re
from pathlib import Path


DOCS = Path(__file__).resolve().parents[1]
ROOT = DOCS.parent
CATALOG = DOCS / "buildings/catalog-coverage.md"
RUNTIME = ROOT / "frontend/public/assets/buildings"
OUTPUT = DOCS / "assets/building-asset-coverage.md"
LOOKUP = (ROOT / "frontend/src/game/renderers/buildingAssetManifests.ts").read_text(encoding="utf-8")
ALIASES = {"field_bed": "windleaf_bed", "road": "ground_road", "standard_road": "common_road"}
REQUIRED_STATES = ("active", "construction", "damaged")


def expected_levels(label: str) -> set[int]:
    numbers = [int(value) for value in re.findall(r"\d+", label)]
    if len(numbers) == 2:
        return set(range(numbers[0], numbers[1] + 1))
    return set(numbers)


def manifest_entries(data: dict) -> list[dict]:
    if isinstance(data.get("items"), list):
        return [entry for entry in data["items"] if isinstance(entry, dict)]
    if isinstance(data.get("assets"), dict):
        return [entry for entry in data["assets"].values() if isinstance(entry, dict)]
    if isinstance(data.get("files"), list):
        return [entry for entry in data["files"] if isinstance(entry, dict)]
    return []


def format_levels(levels: set[int]) -> str:
    return ", ".join(str(level) for level in sorted(levels)) if levels else "—"


def inspect(row: list[str]) -> tuple[str, list[str]]:
    building_id, category, label = [value.strip(" `") for value in row[:3]]
    expected = expected_levels(label)
    asset_id = ALIASES.get(building_id, building_id)
    folder = RUNTIME / category / asset_id
    spec = row[4]
    spec_status = "да" if spec != "нет" else "нет"
    connected = "да" if re.search(r"kind:\s*['\"]" + re.escape(building_id) + r"['\"]", LOOKUP) else "нет"
    manifest_path = folder / "manifest.json"
    if not manifest_path.is_file():
        return f"| `{building_id}` | {label} | {spec_status} | — | — | — | — | — | — | — | {connected} | нет manifest |", [building_id]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return f"| `{building_id}` | {label} | {spec_status} | ошибка JSON | — | — | — | — | — | — | {connected} | ошибка manifest |", [building_id]
    entries = manifest_entries(data)
    declared_states = ", ".join(data.get("states", [])) or "—"
    declared_levels = {int(level) for level in data.get("levels", []) if isinstance(level, int)}
    png_levels = {state: set() for state in REQUIRED_STATES}
    lod_levels = {lod: set() for lod in range(3)}
    problems: list[str] = []
    road = category == "roads" and building_id in {"road", "standard_road", "paved_road"}
    for level in expected:
        for state in REQUIRED_STATES:
            states = ("armed",) if state == "active" and building_id in {"defense_stakes", "defense_resin_snare"} else (state,)
            variants = [entry for entry in entries if entry.get("state") in states and (entry.get("level") == level or road and level in expected)]
            if not variants and not road:
                variants = [entry for entry in entries if entry.get("state") == state and entry.get("level") == level]
            for entry in variants:
                png = entry.get("png")
                if png:
                    path = ROOT / png if str(png).startswith("frontend/") else folder / png
                    if path.is_file() and path.stat().st_size:
                        png_levels[state].add(level)
                for lod in entry.get("lods", []):
                    if lod.get("name") not in {"LOD0", "LOD1", "LOD2"}:
                        continue
                    glb = lod.get("glb")
                    path = ROOT / glb if str(glb).startswith("frontend/") else folder / str(glb)
                    if path.is_file() and path.stat().st_size:
                        lod_levels[int(lod["name"][-1])].add(level)
    blends = list(folder.glob("*.blend"))
    report = bool(list(folder.glob("*report*.json")))
    for state in REQUIRED_STATES:
        if not expected <= png_levels[state]:
            problems.append(state)
    if not all(expected <= lod_levels[lod] for lod in range(3)):
        problems.append("LOD")
    if not blends:
        problems.append("blend")
    if not report:
        problems.append("report")
    if spec_status == "нет":
        problems.append("спека")
    if declared_levels - expected:
        problems.append("лишние уровни " + format_levels(declared_levels - expected))
    if connected == "нет":
        problems.append("lookup")
    status = "полно" if not problems else "нужно: " + ", ".join(problems)
    return (
        f"| `{building_id}` | {label} | {spec_status} | {format_levels(png_levels['active'])} | "
        f"{format_levels(png_levels['construction'])} | {format_levels(png_levels['damaged'])} | "
        f"{format_levels(lod_levels[0])}/{format_levels(lod_levels[1])}/{format_levels(lod_levels[2])} | "
        f"{'да' if blends else 'нет'} | {'да' if report else 'нет'} | {declared_states} | {connected} | {status} |"
    ), ([building_id] if problems else [])


def main() -> None:
    rows = []
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 6:
                rows.append(cells)
    lines = [
        "# Фактическое покрытие игровых ассетов",
        "",
        "Сформировано `python3 docs/assets/scan-building-assets.py` по реестру 21.1 и файлам `frontend/public/assets/buildings/`. Это инвентаризация, а не визуальная приёмка или подтверждение подключения к рендереру. Тестовые и пилотные папки не учитываются. Значения уровней — только непустые файлы, на которые указывает production manifest. Для дорог без номера уровня в имени используется уровень каталога. Три набора после `LOD` соответствуют LOD0/1/2. `ruined` и стадии роста требуют дополнительной проверки по профильной спеке.",
        "",
        "| Игровой ID | Уровни каталога | Спека | PNG active | PNG construction | PNG damaged | GLB LOD0/1/2 | `.blend` | report | Состояния manifest | lookup | Итог |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    incomplete = []
    for row in rows:
        line, problems = inspect(row)
        lines.append(line)
        incomplete.extend(problems)
    lines += [
        "",
        f"Проверено типов: **{len(rows)}**; с неполным набором или без production manifest: **{len(incomplete)}**.",
        "",
        "## Перед передачей в production",
        "",
        "- Для каждой обязательной пары `building_id × level × state` сверить geometry, alpha, footprint, anchor, материалы и три LOD по [визуальному контракту](building-asset-contract.md).",
        "- `lookup` означает наличие `kind` в `buildingAssetManifests.ts`; карту и 3D-просмотр дополнительно проверить сценарием, поскольку статическая запись ещё не доказывает успешную загрузку.",
        "- Для полей дополнительно проверить стадии роста и супер-версию; для дорог и стен — формы стыков; для разрушимых объектов — `ruined` либо утверждённый fallback.",
        "- Удалять или переносить тестовые варианты только после принятия production-семейства и проверки ссылок.",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
