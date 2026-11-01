"""Синхронизация спецификаций XP с серверным каталогом: --write или --check."""

import argparse
import json
import re
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "backend/internal/domain/catalog/building_xp.json"
START = "<!-- runtime-xp:start -->"
END = "<!-- runtime-xp:end -->"


def render(entries):
    lines = [START, "## Действующие награды XP", "",
             "Источник: `backend/internal/domain/catalog/building_xp.json`. Эта таблица имеет приоритет над прежними проектными числами XP ниже в документе.", "",
             "Награда за создание/апгрейд выдаётся владельцу после успешного завершения, по итоговому типу и уровню. Это одна награда, а не сумма наград за начало и конец действия. При переходе к другому типу используется таблица нового типа.", "",
             "XP за уничтожение чужой постройки получает игрок, нанёсший последний удар оружием, или создатель добившего монстра. Урон без уничтожения, снос своего здания, дикие монстры и повторная обработка награду не дают.", "",
             "Работа — один сбор урожая/продукции; суперурожай даёт тройной XP. Ноль означает отсутствие отдельной награды за работу. Ремонт, перенос, отмена, перезарядка и переключение защиты отдельно XP не дают; защитные убийства диких монстров сохраняют свою награду."]
    for kind, rows in entries.items():
        lines += ["", f"### `{kind}`", "",
                  "| Уровень | XP за создание / завершение апгрейда | XP за работу | XP за уничтожение чужой постройки |",
                  "| ---: | ---: | ---: | ---: |"]
        for r in rows:
            lines.append(f"| {r['level']} | {r['completion']} | {r['work']} | {r['destruction']} |")
        if kind == "town_hall":
            lines += ["", "Бесплатный мгновенный первый уровень даёт XP за создание только один раз за жизнь игрока, независимо от ID ратуши. Повторное строительство после сноса не создаёт бесконечный источник опыта; улучшения награждаются обычным образом."]
        if kind in {"mine", "rope_yard"}:
            lines += ["", "XP за работу выдаётся при успешном сборе партии: `mine_run` для шахты, `rope_yard_run` для канатного двора. Рецепты всех уровней хранятся в `data/balance/v2.json`."]
    return "\n".join(lines + [END])


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    xp = json.loads(CATALOG.read_text())
    assert xp["schema_version"] == 1
    xp = xp["buildings"]
    buildings = json.loads((ROOT / "data/buildings/catalog-v2.json").read_text())["buildings"]
    runtime = json.loads((ROOT / "backend/internal/domain/catalog/balance.v2.json").read_text())
    expected = {b["type"]: {r["level"] for r in b.get("upgradeLevels") or [b]} for b in buildings}
    expected.update({kind: {r["Level"]} for kind, r in runtime["ruins"].items()})
    assert set(expected) == set(xp), "XP должен покрывать каждый тип и только существующие типы"
    working = {b["type"] for b in buildings if b["category"] == "fields"}
    working.update(r["BuildingType"] for r in runtime["recipes"])
    working.add("oil_well")
    destruction_rewards = set()
    completion_rewards = set()
    for kind, levels in expected.items():
        rows = xp[kind]
        assert len(rows) == len(levels) and {r["level"] for r in rows} == levels, kind
        assert all(r["completion"] > 0 and 0 < r["destruction"] <= 500000 and r["work"] >= 0 for r in rows), kind
        assert kind not in working or all(r["work"] > 0 for r in rows), kind
        assert all(a["destruction"] < b["destruction"] for a, b in zip(rows, rows[1:])), kind
        for row in rows:
            value = row["destruction"]
            assert value % 5 and value not in destruction_rewards, (kind, row["level"], "повтор/круглый XP уничтожения")
            destruction_rewards.add(value)
            value = row["completion"]
            if value >= 100:
                assert value % 5 and value not in completion_rewards, (kind, row["level"], "повтор/круглый XP завершения")
                completion_rewards.add(value)
    paths = runpy.run_path(str(ROOT / "docs/buildings/sync-runtime-tables.py"))["documents"]()
    grouped = {path: {kind: xp[kind]} for kind, path in paths.items()}
    grouped[ROOT / "docs/buildings/ruins/endgame-restoration.md"] = {kind: xp[kind] for kind in runtime["ruins"]}
    grouped[ROOT / "docs/buildings/industry/oil-well.md"] = {"oil_well": xp["oil_well"]}
    stale = []
    for path, entries in grouped.items():
        source = path.read_text()
        section = render(entries)
        if START in source:
            updated = re.sub(re.escape(START) + r"[\s\S]*?" + re.escape(END), lambda _: section, source, count=1)
        else:
            heading = re.search(r"^# .+$", source, re.M)
            assert heading, path
            updated = source[:heading.end()] + "\n\n" + section + source[heading.end():]
        if source != updated:
            stale.append(str(path.relative_to(ROOT)))
            if args.write:
                path.write_text(updated)
    if args.check and stale:
        raise SystemExit("Устарели таблицы XP: " + ", ".join(stale))
    print(f"Проверено {len(xp)} типов, {sum(map(len, xp.values()))} уровней, {len(grouped)} документов; обновлено {len(stale) if args.write else 0}")


if __name__ == "__main__":
    main()
