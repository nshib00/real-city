"""Создаёт исходные визуальные спеки для ID без файла в реестре 21.1.

Результат требует художественной проверки до запуска Blender. Существующие файлы
никогда не перезаписываются. Запуск: python3 docs/assets/generate-missing-building-specs.py
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
DOCS = HERE.parent
ROOT = DOCS.parent
CATALOG = {item["type"]: item for item in json.loads(subprocess.check_output(["node", str(DOCS / "buildings/export-shared-catalog.cjs")], text=True))["buildings"]}
TEMPLATE = yaml.safe_load((HERE / "specs/template.yaml").read_text(encoding="utf-8"))
ALIASES = {"field_bed": "windleaf_bed", "road": "ground_road", "standard_road": "common_road"}

# Уникальная форма и детали семейства. Полные цены и игровые уровни берутся из каталога.
BLUEPRINTS = {
    "stone_house": ("Каменный дом с зелёной черепицей, входом и обжитым двором", "слуховое окно, каменная пристройка, крыльцо"),
    "apartment_house": ("Плотный жилой дом с общим двором и несколькими входами", "балконы, этаж, общая лестница"),
    "palace": ("Светлый дворец с жилым корпусом и садом", "галерея, балкон, крытая арка"),
    "residential_skyscraper": ("Высокий жилой корпус из камня, металла и стекла", "террасы, вертикальные окна, технический этаж"),
    "workshop": ("Небольшая ремесленная мастерская с рабочим столом и навесом", "производственный стол, склад заготовок, дымоход"),
    "brick_kiln": ("Низкая кирпичная печь и ряды сушащихся заготовок", "топливный отсек, стеллаж, вытяжка"),
    "glass_workshop": ("Светлая печь, стойки охлаждения и голубоватые листы стекла", "тигель, вытяжка, сортировочный стол"),
    "forge": ("Открытый горн, наковальня и защищённое место кузнеца", "мехи, стойка инструментов, угольный короб"),
    "dye_works": ("Красильный цех с раздельными цветными чанами", "сушильная рама, ткацкие образцы, навес"),
    "optical_workshop": ("Точный верстак с линзами и медными оправами", "шлифовальный круг, приборная стойка, стеклянный шкаф"),
    "mint": ("Компактный монетный двор с прессом и запертой кассой", "штемпель, сейф, охраняемая дверь"),
    "warehouse": ("Деревянный склад с каменным цоколем и запертой дверью", "раздельные стеллажи, навес, подъёмный блок"),
    "coin_storage": ("Городское хранилище монет с видимой защищённой кассой", "сейфовая дверь, счётчик, крытая секция"),
    "market": ("Открытый торговый двор с весами и прилавками", "навес, торговая вывеска, закрытый товарный ящик"),
    "alliance_house": ("Союзный дом собраний с общим флагом и доской объявлений", "зал совета, архивный шкаф, крыльцо"),
    "road": ("Грунтовая дорога с ровной изометрической основой", "утрамбованный след, край травы, дорожный стык"),
    "standard_road": ("Укреплённая дорога из досок и камня", "каменный бордюр, укреплённый настил, стык"),
    "paved_road": ("Мощёная дорога с крупной читаемой кладкой", "каменный шов, обочина, стык"),
    "field_bed": ("Грядка ветролиста с резными опорами и широкими листьями", "ростовые ряды, цветовая метка, редкий лист"),
    "seed_garden": ("Семенной огород с несколькими сортировочными секциями", "лотки, таблички, семенные мешочки"),
    "flax_field": ("Льняное поле с прямыми узкими рядами и светлым волокном", "опоры для льна, связки, сушильная стойка"),
    "sugar_bed": ("Грядка сахарного тростника с высокими перевязанными стеблями", "связки, подпорки, корзина урожая"),
    "lumber_yard": ("Лесопильный двор с брёвнами и механизмом распила", "пильная рама, штабель досок, крытый склад"),
    "sand_quarry": ("Песчаный карьер с выемкой и погрузочной тележкой", "ступень выемки, рельс, сортировочная куча"),
    "mine": ("Шахтный вход в горный массив с крепями и вагонеткой", "укреплённая штольня, лебёдка, рудный склад"),
    "iron_mine": ("Железный рудник с красноватой рудой и деревянными крепями", "вагонетка, лебёдка, рудные глыбы"),
    "stone_cutters": ("Камнетёсный двор с крупными блоками и рабочей пилой", "станок, штабель блоков, каменная пыль"),
    "rope_yard": ("Канатный двор с длинными натянутыми прядями", "крутильный привод, бобины, склад верёвок"),
    "chemical_workshop": ("Химическая мастерская с закрытыми реакторами и трубками", "вытяжка, защитный экран, сосуды"),
    "precision_workshop": ("Завод точной механики с калибровочным станком", "измерительный стол, закрытый сборочный пост, приборы"),
}

RESOURCE_VISUAL = {
    "coins": "аккуратность фасада и защищённый учёт вложений",
    "wood": "деревянные опоры, брусья и склад материала",
    "planks": "дощатые настилы, стойки и рабочие поверхности",
    "stone": "крупные камни фундамента и низкие стены",
    "stone_block": "тёсаные блоки цоколя и силовых опор",
    "brick": "кирпичная кладка и дымоход",
    "glass": "крупные окна и защищённые стеклянные панели",
    "metal": "обвязка рамы и рабочий механизм",
    "iron_ingot": "железные крепления, петли и рабочий привод",
    "steel": "силовые балки и защищённый кожух",
    "reinforced_concrete": "железобетонное основание и несущие узлы",
    "reinforced_beams": "толстые несущие поперечины",
    "mechanism": "видимый зубчатый привод",
    "electronics": "контрольные приборы и безопасная проводка",
    "armor_plates": "защитные пластины на уязвимом узле",
    "fabric": "тканевый навес и функциональные тенты",
    "rope": "натянутые стяжки и подъёмные канаты",
    "clay": "глиняные формы и сырьевые лотки",
    "coal": "закрытый угольный короб и топка",
    "sand": "светлый песок и заполненные сырьевые ящики",
    "oil": "герметичные тёмные резервуары и трубы",
    "fuel": "закрытые топливные баки и предупреждающая метка",
}

FIELD_FEATURES = ["первый ряд", "дополнительные секции", "крупные ростки", "разделитель рядов", "сортировочная зона", "усиленный бортик", "дополнительные опоры", "поливная линия", "контрольная стойка", "редкий акцент", "финальная садовая секция"]
BUILDING_FEATURES = ["основной корпус", "дополнительная опора", "рабочий навес", "защищённый склад", "механический узел", "второй объём", "каменная секция", "усиленный портал", "приборная зона", "закрытая подача", "высокий сигнал", "поздняя отделка", "завершённая силовая рама"]


def coverage_rows() -> list[list[str]]:
    rows = []
    for line in (DOCS / "buildings/catalog-coverage.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("| `"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells[4] == "нет":
                rows.append(cells)
    return rows


def main() -> None:
    for cells in coverage_rows():
        building_id = cells[0].strip("`")
        item = CATALOG[building_id]
        category = item["category"]
        asset_id = building_id
        runtime_id = ALIASES.get(building_id, building_id)
        spec = copy.deepcopy(TEMPLATE)
        spec["asset_id"] = asset_id
        spec["category"] = category
        spec["catalog_status"] = "registered"
        spec["display_name"] = item["name"]
        spec["footprint"] = item["footprint"]
        spec["levels"] = []
        levels = item.get("upgradeLevels") or [item]
        shape, details = BLUEPRINTS[building_id]
        features = FIELD_FEATURES if category == "fields" else BUILDING_FEATURES
        all_materials: dict[str, list[int]] = {}
        for level_item in levels:
            level = level_item["level"]
            resources = list(dict.fromkeys(part["resource"] for part in level_item["cost"]))
            for resource in resources:
                all_materials.setdefault(resource, []).append(level)
            feature = features[min(len(spec["levels"]), len(features) - 1)]
            spec["levels"].append({
                "level": level,
                "visual_goal": f"{shape}; уровень {level} добавляет {feature}. Крупные детали: {details}.",
                "cost_resources": resources,
                "triangle_budget": {"min": 700 + 100 * len(spec["levels"]), "max": 4500 + 500 * len(spec["levels"])},
                "adds": [feature.replace(" ", "_"), details.split(", ")[0].replace(" ", "_")],
                "constraints": ["Все элементы остаются внутри игрового footprint; камера и основание постоянны."],
            })
        spec["material_map"] = {
            resource: {"visible_as": RESOURCE_VISUAL.get(resource, f"малый читаемый акцент ресурса {resource} в конструкции или продукции"),
                       "levels": sorted(set(level_numbers)), "priority": "accent" if resource == "coins" else "secondary"}
            for resource, level_numbers in all_materials.items()
        } or {"wood": {"visible_as": "деревянный рабочий элемент", "levels": [level["level"] for level in levels], "priority": "primary"}}
        spec["level_progression"]["mass"]["rule"] = f"Сохранять силуэт «{shape}»; каждый следующий уровень добавляет реальный объём или узел."
        spec["level_progression"]["materials"]["rule"] = "Материалы появляются не раньше уровня, где они есть в цене строительства."
        spec["level_progression"]["props"]["rule"] = f"Крупные детали семейства: {details}; мелкий шум не маскирует вход."
        spec["level_progression"]["late_elements"]["rule"] = "Поздние узлы усиливают основную функцию, не меняя идентичность семейства."
        spec["state_policy"]["active"]["rule"] = f"Готовый объект: {shape}; рабочие детали чисты и читаемы."
        spec["state_policy"]["construction"]["rule"] = "Незавершённый каркас целевого уровня, не установлен один крупный функциональный узел."
        spec["state_policy"]["damaged"]["rule"] = "Сломан крупный функциональный узел, силуэт и ориентация входа сохраняются."
        spec["state_policy"]["ruined"] = {"rule": "Остатки корпуса и материалов читаются как тот же объект, не активная постройка."}
        spec["states"] = ["active", "construction", "damaged", "ruined"]
        if category == "fields":
            spec["states"] += [f"stage{index:02d}" for index in range(1, 5)]
            spec["states"] += [f"super_stage{index:02d}" for index in range(1, 7)]
        if category == "roads":
            spec["notes"] = ["Для каждой формы соседства нужны single/end/straight/corner/T/cross; один уровень не заменяет набор из 16 стыков."]
        else:
            spec["notes"] = ["Первичная visual-spec по действующему каталогу; художественную приёмку и генерацию выполнять по контракту 22.2."]
        spec["lod_policy"]["chain"][0]["triangle_budget"] = {"min": 700, "max": 4500 + 500 * (len(levels) - 1)}
        spec["lod_policy"]["chain"][1]["triangle_budget"] = {"min": 350, "max": 2200 + 250 * (len(levels) - 1)}
        spec["lod_policy"]["chain"][2]["triangle_budget"] = {"min": 150, "max": 1100 + 125 * (len(levels) - 1)}
        spec["output"]["runtime_dir"] = f"frontend/public/assets/buildings/{category}/{runtime_id}"
        spec["output"]["source_dir"] = f"frontend/src/assets/buildings/{category}/{runtime_id}"
        text_link = re.search(r"\]\(([^)]+)\)", cells[3]).group(1)
        spec["references"]["docs"] = [f"docs/buildings/{text_link}"]
        spec["references"]["art_guide"] = "docs/art/visual-style-guide.md"
        output = HERE / "specs" / category / f"{asset_id}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise FileExistsError(output)
        output.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(output.relative_to(DOCS))


if __name__ == "__main__":
    main()
