"""Проверка замыкания ресурсов рецептов для явно заданных внешних источников.

Не доказывает достижимость от стартового состояния: уровни, стройка, рабочие,
случайные награды и количество ресурсов требуют отдельной серверной проверки.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def closure(recipes, sources):
    available = {resource: f"external:{resource}" for resource in sources}
    reached = set()
    while True:
        changed = False
        for recipe in recipes:
            required = {item["Resource"] for item in recipe.get("Input") or []}
            if recipe.get("FuelPerRun", 0):
                required.add("fuel")
            if not required <= available.keys():
                continue
            reached.add((recipe["ID"], recipe.get("RequiredLevel", 0)))
            for output in recipe.get("Output") or []:
                resource = output["Resource"]
                if resource not in available:
                    available[resource] = recipe["ID"]
                    changed = True
        if not changed:
            break
    blocked = []
    for recipe in recipes:
        key = (recipe["ID"], recipe.get("RequiredLevel", 0))
        if key in reached:
            continue
        required = {item["Resource"] for item in recipe.get("Input") or []}
        if recipe.get("FuelPerRun", 0):
            required.add("fuel")
        blocked.append({"recipe": key[0], "level": key[1], "missing": sorted(required - available.keys())})
    return {"sources": sorted(sources), "resource_producers": available, "blocked": blocked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", required=True, help="JSON-массив ресурсов из проверенных внешних источников")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    balance = json.loads((ROOT / "data/balance/v2.json").read_text())
    sources = json.loads(Path(args.sources).read_text())
    known = {item["Type"] for item in balance["resources"]}
    if not isinstance(sources, list) or not all(isinstance(item, str) and item in known for item in sources):
        parser.error("sources должен быть массивом известных ресурсов")
    recipes = {(r["ID"], r["RequiredLevel"]): r for r in balance["recipes"]}
    for variants in balance["recipe_levels"].values():
        for recipe in variants:
            recipes[(recipe["ID"], recipe["RequiredLevel"])] = recipe
    report = closure(list(recipes.values()), set(sources))
    report["scope"] = "guaranteed recipe outputs only; excludes building, worker, quantity and random reward reachability"
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Рецептов/уровней: {len(recipes)}; заблокировано: {len(report['blocked'])}")


if __name__ == "__main__":
    main()
