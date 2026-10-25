"""Сверяет поуровневый баланс shared и backend и пишет отчёт для 21.12.

Требуется установленный frontend/node_modules/typescript. Запуск:
python3 docs/buildings/audit-catalogs.py
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "catalog-parity.md"


def parse_backend() -> dict[str, dict]:
    env = dict(os.environ)
    env.setdefault("GOCACHE", "/tmp/real-city-go-cache")
    return json.loads(subprocess.check_output(
        ["go", "run", "./cmd/catalog-export"], cwd=ROOT / "backend", text=True, env=env
    ))


def main() -> None:
    shared = json.loads(subprocess.check_output(["node", str(HERE / "export-shared-catalog.cjs")], text=True))
    backend = parse_backend()
    findings = []
    rows = []
    for item in shared["buildings"]:
        type_id = item["type"]
        server = backend.get(type_id)
        if server is None:
            findings.append(f"`{type_id}`: отсутствует в backend")
            continue
        issues = []
        for key in ("name", "category"):
            if item[key] != server[key]:
                issues.append(f"{key}: shared={item[key]!r}, backend={server[key]!r}")
        if server["footprint"] is not None and item["footprint"] != server["footprint"]:
            issues.append(f"footprint: shared={item['footprint']}, backend={server['footprint']}")
        if set(item["upgradeTo"]) != set(server["upgradeTo"]):
            issues.append(f"upgradeTo: shared={item['upgradeTo']}, backend={server['upgradeTo']}")
        frontend_levels = item.get("upgradeLevels") or [item]
        shared_levels = {int(level["level"]): level for level in frontend_levels}
        server_levels = {int(level["level"]): level for level in server["levels"]}
        if shared_levels.keys() != server_levels.keys():
            issues.append(f"уровни: shared={sorted(shared_levels)}, backend={sorted(server_levels)}")
        for level in sorted(shared_levels.keys() & server_levels.keys()):
            a, b = shared_levels[level], server_levels[level]
            for key in ("buildSeconds", "population"):
                if a.get(key) != b.get(key):
                    issues.append(f"L{level} {key}: {a.get(key)} != {b.get(key)}")
            if a.get("health", 0) != b.get("health", 0):
                issues.append(f"L{level} health: {a.get('health', 0)} != {b.get('health', 0)}")
            a_cost = {part["resource"]: part["amount"] for part in a["cost"]}
            if a_cost != b["cost"]:
                issues.append(f"L{level} стоимость: shared={a_cost}, backend={b['cost']}")
        if issues:
            findings.extend(f"`{type_id}`: {issue}" for issue in issues)
        rows.append(f"| `{type_id}` | {len(shared_levels)} | {'совпадает' if not issues else '; '.join(issues)} |")
    for type_id in sorted(backend.keys() - {item["type"] for item in shared["buildings"]}):
        findings.append(f"`{type_id}`: отсутствует в shared")
    report = [
        "# Сверка игрового каталога построек",
        "",
        "Отчёт сформирован `python3 docs/buildings/audit-catalogs.py`. Сравниваются ID, русское имя, категория, размер клетки, переходы апгрейда и **каждый игровой уровень**: время в секундах, строители, HP и стоимость по `resource_id`. Frontend импортирует generated `shared/catalog/buildings.ts`, а API `/api/v1/buildings/catalog` отдаёт runtime backend-каталог; оба используют `data/buildings/catalog-v2.json`. Текстовые документы и экранные описания требуют отдельной редакторской сверки.",
        "",
        "| ID | Число уровней | Shared ↔ backend |",
        "| --- | ---: | --- |",
        *rows,
        "",
        f"Типов shared: **{len(shared['buildings'])}**; backend: **{len(backend)}**; расхождений: **{len(findings)}**.",
        "",
        "## Расхождения и решения",
        "",
    ]
    report += [f"- {issue}" for issue in findings] or ["- Числовых расхождений между каталогами не найдено. Проектные поля текстовых документов не становятся игровыми автоматически."]
    report += ["", "## Оставшаяся редакторская проверка", "", "- Сопоставить каждую числовую таблицу индивидуального документа с соответствующей строкой каталога. Особенно важны ранние дома, хранилище монет, ратуша, поля и проектные уровни позднего жилья.", "- Сверить тексты карточек frontend: некоторые описания обещают выпуск у зданий без зарегистрированного серверного рецепта. До реализации рецепта показывать их как проектную роль.", "- Проверить русские единицы: `buildSeconds` — секунды, `population` — строители, `FuelPerRun` — бензин на цикл; количество ресурса всегда целое.", ""]
    OUT.write_text("\n".join(report), encoding="utf-8")
    print(f"shared={len(shared['buildings'])} backend={len(backend)} findings={len(findings)}")
    for issue in findings[:15]:
        print(issue)


if __name__ == "__main__":
    main()
