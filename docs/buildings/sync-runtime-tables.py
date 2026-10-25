"""Поддерживает действующие игровые цифры в каждом основном документе постройки.

python3 docs/buildings/sync-runtime-tables.py --write
python3 docs/buildings/sync-runtime-tables.py --check
"""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/buildings"
REGISTER = DOCS / "catalog-coverage.md"
CATALOG = ROOT / "data/buildings/catalog-v2.json"
START = "<!-- runtime-catalog:start -->"
END = "<!-- runtime-catalog:end -->"


def documents():
    result = {}
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\| `([^`]+)` \|[^\n]*?\]\(([^)]+\.md)\)", line)
        if match:
            result[match.group(1)] = (DOCS / match.group(2)).resolve()
    return result


def render(item):
    levels = item.get("upgradeLevels") or [item]
    availability = "Можно построить напрямую." if item["firstLevel"] else "Получается через улучшение предыдущей постройки."
    paths = ", ".join(f"`{name}`" for name in item["upgradeTo"]) or "нет"
    lines = [
        START,
        "## Действующие игровые параметры",
        "",
        f"Игровой ID: `{item['type']}`. Категория: `{item['category']}`. Название в интерфейсе: **{item['name']}**. Занимает {item['footprint']['width']}×{item['footprint']['height']} клеток. {availability} Переходы к другим типам: {paths}.",
        "",
        "| Уровень | Время, с | Строители | HP | Стоимость по ID ресурса |",
        "| ---: | ---: | ---: | ---: | --- |",
    ]
    for level in levels:
        cost = ", ".join(f"{entry['amount']} × `{entry['resource']}`" for entry in level["cost"]) or "бесплатно"
        lines.append(f"| {level['level']} | {level['buildSeconds']} | {level['population']} | {level.get('health', 0)} | {cost} |")
    lines += [
        "",
        "Источник этих значений — `data/buildings/catalog-v2.json`. Другие числовые варианты ниже в документе относятся к проектным предложениям до отдельного переноса в игровой каталог.",
        END,
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    items = json.loads(CATALOG.read_text(encoding="utf-8"))["buildings"]
    paths = documents()
    if {item["type"] for item in items} != set(paths):
        raise SystemExit("реестр документов расходится с игровыми ID")
    stale = []
    for item in items:
        path = paths[item["type"]]
        if not path.is_relative_to(DOCS) or not path.is_file():
            raise SystemExit(f"документ недоступен: {path}")
        source = path.read_text(encoding="utf-8")
        section = render(item)
        if START in source and END in source:
            updated = re.sub(re.escape(START) + r"[\s\S]*?" + re.escape(END), lambda _: section, source, count=1)
        else:
            heading = re.search(r"^# .+$", source, re.MULTILINE)
            if not heading:
                raise SystemExit(f"нет заголовка: {path}")
            updated = source[:heading.end()] + "\n\n" + section + source[heading.end():]
        if source != updated:
            stale.append(path.relative_to(ROOT).as_posix())
            if args.write:
                path.write_text(updated, encoding="utf-8")
    if args.check and stale:
        raise SystemExit(f"устаревшие runtime-таблицы ({len(stale)}): " + ", ".join(stale[:10]))
    print(f"Проверено {len(items)} документов; обновлено {len(stale) if args.write else 0}")


if __name__ == "__main__":
    main()
