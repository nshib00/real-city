# Реестр покрытия построек

**Актуализация 25 октября 2026:** каталог содержит 72 ID. Во всех 72 основных документах есть действующая таблица каждого уровня из канонического JSON. `make catalog-check` сверяет таблицы, shared/backend и проверяет схему баланса. API `GET /api/v1/buildings/catalog?scope=all` раскрывает те же 72 типа и уровни. Исходная числовая проверка приведена в [отчёте сверки](catalog-parity.md).

Фактическое наличие `.blend`, PNG, LOD, manifest, report и frontend lookup по каждому игровому уровню сверяется в [реестре ассетов](../assets/building-asset-coverage.md), который обновляется скриптом `python3 docs/assets/scan-building-assets.py`.

Снимок каталогов на 25 октября 2026 года. Источник игровых ID и уровней — `data/buildings/catalog-v1.json`; из него генерируется `shared/catalog/buildings.ts`, а backend читает встроенную копию. Наличие ID перепроверено по `backend/internal/domain/building/building.go`. В обоих runtime-каталогах **72 одинаковых ID**, отсутствующих или повторяющихся игровых ID нет. Каждому ID сопоставлен один основной текстовый документ. Числа уровней ниже отражают каталог, а не обещание полноты моделей.

В колонках «Визуальная спека» и «Runtime manifest» указано лишь наличие основного файла. Это не подтверждает все уровни, состояния, успешную сборку или подключение в рендерере. Тестовые `villa_*test`, `*_v2`, `backup_*` и `*_pilot` не считаются production. Теперь **все 72 ID имеют основную визуальную и текстовую спеку**, в том числе 32 визуальных черновика для художественной приёмки; **50 типов имеют runtime manifest**. Для `defense_cannon` существуют два формата визуальной спеки (`.yaml` и `.json`), их нужно свести к одному источнику до автоматической генерации. Старые пометки «сверить числа» в колонке «Проверка» относятся к редактуре проектного текста и механике; действующие числа в таблицах выше уже синхронизированы.

После исходного снимка добавлен production manifest для `siege_yard` (1 ноября 2026); число типов с runtime manifest в таблице теперь **51**.

| Игровой ID | Категория | Уровни каталога | Основной текст | Визуальная спека | Runtime manifest | Проверка |
| --- | --- | ---: | --- | --- | --- | --- |
| `town_hall` | center | 1–15 | [town-hall.md](center/town-hall.md) | [town_hall.yaml](../assets/specs/center/town_hall.yaml) | есть | уровни и параметры сверены с каталогом |
| `dugout` | housing | 1–5 | [dugout.md](houses/dugout.md) | [dugout.yaml](../assets/specs/housing/dugout.yaml) | нет | сверить числа |
| `wood_house` | housing | 1–6 | [wood-house.md](houses/wood-house.md) | [wood_house.yaml](../assets/specs/housing/wood_house.yaml) | нет | сверить числа |
| `stone_house` | housing | 1–6 | [stone-house.md](houses/stone-house.md) | [stone_house.json](../assets/specs/housing/stone_house.json) | есть | баланс и модели уровней 1–6 |
| `apartment_house` | housing | 1 | [apartment-house.md](houses/apartment-house.md) | [apartment_house.json](../assets/specs/housing/apartment_house.json) | нет | ветка после каменного дома |
| `villa` | housing | 1–5 | [villa.md](houses/villa.md) | [villa_production.yaml](../assets/specs/housing/villa_production.yaml) | есть | игровая ветка уровней 1–5 |
| `palace` | housing | 5 | [palace.md](houses/palace.md) | [palace.json](../assets/specs/housing/palace.json) | нет | есть проектные поля |
| `residential_skyscraper` | housing | 5 | [residential-skyscraper.md](houses/residential-skyscraper.md) | [residential_skyscraper.json](../assets/specs/housing/residential_skyscraper.json) | нет | есть проектные поля |
| `workshop` | industry | 1 | [workshop.md](industry/workshop.md) | [workshop.json](../assets/specs/industry/workshop.json) | нет | есть проектные поля |
| `brick_kiln` | industry | 1 | [brick-kiln.md](industry/brick-kiln.md) | [brick_kiln.json](../assets/specs/industry/brick_kiln.json) | нет | есть проектные поля |
| `brick_yard` | industry | 1–10 | [brick-yard.md](industry/brick-yard.md) | [brick_yard.json](../assets/specs/industry/brick_yard.json) | есть | есть проектные поля |
| `glass_workshop` | industry | 1–12 | [glass-workshop.md](industry/glass-workshop.md) | [glass_workshop.json](../assets/specs/industry/glass_workshop.json) | есть | модели и баланс уровней 1–12 |
| `forge` | industry | 1 | [forge.md](industry/forge.md) | [forge.json](../assets/specs/industry/forge.json) | нет | есть проектные поля |
| `weaving_yard` | industry | 1–10 | [weaving-yard.md](industry/weaving-yard.md) | [weaving_yard.json](../assets/specs/industry/weaving_yard.json) | есть | есть проектные поля |
| `dye_works` | industry | 1 | [dye-works.md](industry/dye-works.md) | [dye_works.json](../assets/specs/industry/dye_works.json) | есть | есть проектные поля |
| `mechanical_workshop` | industry | 1–10 | [mechanical-workshop.md](industry/mechanical-workshop.md) | [mechanical_workshop.json](../assets/specs/industry/mechanical_workshop.json) | есть | есть проектные поля |
| `optical_workshop` | industry | 1 | [optical-workshop.md](industry/optical-workshop.md) | [optical_workshop.json](../assets/specs/industry/optical_workshop.json) | нет | есть проектные поля |
| `mint` | industry | 1 | [mint.md](industry/mint.md) | [mint.json](../assets/specs/industry/mint.json) | нет | есть проектные поля |
| `coin_storage` | storage | 1–12 | [coin-storage.md](storage/coin-storage.md) | [coin_storage.json](../assets/specs/storage/coin_storage.json) | есть | сверить числа |
| `market` | trade | 1 | [market.md](trade/market.md) | [market.json](../assets/specs/trade/market.json) | нет | есть проектные поля |
| `tower` | defense | 1 | [tower.md](defense/tower.md) | [tower.json](../assets/specs/defense/tower.json) | есть | сверить механику |
| `defense_cannon` | defense | 1–12 | [cannon.md](defense/cannon.md) | [defense_cannon.yaml](../assets/specs/defense/defense_cannon.yaml) | есть | есть проектные поля |
| `defense_stakes` | defense | 1–6 | [stakes.md](defense/stakes.md) | [defense_stakes.json](../assets/specs/defense/defense_stakes.json) | есть | есть проектные поля |
| `defense_resin_snare` | defense | 1–4 | [resin-snare.md](defense/resin-snare.md) | [defense_resin_snare.json](../assets/specs/defense/defense_resin_snare.json) | есть | есть проектные поля |
| `defense_bolt_thrower` | defense | 1–8 | [bolt-thrower.md](defense/bolt-thrower.md) | [defense_bolt_thrower.json](../assets/specs/defense/defense_bolt_thrower.json) | есть | есть проектные поля |
| `defense_storm_coil` | defense | 1–6 | [storm-coil.md](defense/storm-coil.md) | [defense_storm_coil.json](../assets/specs/defense/defense_storm_coil.json) | есть | есть проектные поля |
| `defense_automaton_bay` | defense | 1–5 | [automaton-bay.md](defense/automaton-bay.md) | [defense_automaton_bay.json](../assets/specs/defense/defense_automaton_bay.json) | есть | есть проектные поля |
| `defense_guardian_enclosure` | defense | 1–5 | [guardian-enclosure.md](defense/guardian-enclosure.md) | [defense_guardian_enclosure.json](../assets/specs/defense/defense_guardian_enclosure.json) | есть | есть проектные поля |
| `wooden_wall` | defense | 1–3 | [wooden-wall.md](roads/wooden-wall.md) | [wooden_wall.json](../assets/specs/roads/wooden_wall.json) | есть | сверить механику |
| `stone_wall` | defense | 4–7 | [stone-wall.md](roads/stone-wall.md) | [stone_wall.json](../assets/specs/roads/stone_wall.json) | есть | сверить механику |
| `concrete_wall` | defense | 8–10 | [concrete-wall.md](defense/concrete-wall.md) | [concrete_wall.json](../assets/specs/roads/concrete_wall.json) | есть | сверить механику |
| `modern_wall` | defense | 11–13 | [modern-wall.md](defense/modern-wall.md) | [modern_wall.json](../assets/specs/roads/modern_wall.json) | есть | сверить механику |
| `road` | roads | 1 | [ground-road.md](roads/ground-road.md) | [road.json](../assets/specs/roads/road.json) | есть | сверить механику |
| `standard_road` | roads | 2 | [common-road.md](roads/common-road.md) | [standard_road.json](../assets/specs/roads/standard_road.json) | есть | сверить механику |
| `paved_road` | roads | 3 | [paved-road.md](roads/paved-road.md) | [paved_road.json](../assets/specs/roads/paved_road.json) | есть | сверить механику |
| `alliance_house` | social | 1 | [alliance-house.md](social/alliance-house.md) | [alliance_house.json](../assets/specs/social/alliance_house.json) | нет | сверить числа |
| `field_bed` | fields | 1–11 | [windleaf-bed.md](fields/windleaf-bed.md) | [field_bed.json](../assets/specs/fields/field_bed.json) | есть | сверить числа |
| `seed_garden` | fields | 1–10 | [seed-garden.md](fields/seed-garden.md) | [seed_garden.json](../assets/specs/fields/seed_garden.json) | есть | есть проектные поля |
| `herb_bed` | fields | 1–9 | [herb-bed.md](fields/herb-bed.md) | [herb_bed.yaml](../assets/specs/fields/herb_bed.yaml) | есть | есть проектные поля |
| `mushroom_grove` | fields | 1–10 | [mushroom-grove.md](fields/mushroom-grove.md) | [mushroom_grove.yaml](../assets/specs/fields/mushroom_grove.yaml) | есть | сверить числа |
| `flax_field` | fields | 1–10 | [flax-field.md](fields/flax-field.md) | [flax_field.json](../assets/specs/fields/flax_field.json) | есть | сверить числа |
| `reed_bed` | fields | 1–10 | [reed-bed.md](fields/reed-bed.md) | [reed_bed.yaml](../assets/specs/fields/reed_bed.yaml) | есть | сверить числа |
| `dye_garden` | fields | 1–6 | [dye-garden.md](fields/dye-garden.md) | [dye_garden.json](../assets/specs/fields/dye_garden.json) | есть | сверить числа |
| `oilseed_field` | fields | 1–7 | [oilseed-field.md](fields/oilseed-field.md) | [oilseed_field.yaml](../assets/specs/fields/oilseed_field.yaml) | есть | сверить числа |
| `sugar_bed` | fields | 1–9 | [sugar-bed.md](fields/sugar-bed.md) | [sugar_bed.json](../assets/specs/fields/sugar_bed.json) | нет | сверить числа |
| `crystal_greenhouse` | fields | 1–4 | [crystal-greenhouse.md](fields/crystal-greenhouse.md) | [crystal_greenhouse.json](../assets/specs/fields/crystal_greenhouse.json) | есть | сверить числа |
| `lumber_yard` | industry | 1–13 | [sawmill-yard.md](industry/sawmill-yard.md) | [lumber_yard.json](../assets/specs/industry/lumber_yard.json) | нет | есть проектные поля |
| `sand_quarry` | industry | 1–11 | [sand-quarry.md](industry/sand-quarry.md) | [sand_quarry.json](../assets/specs/industry/sand_quarry.json) | есть | есть проектные поля |
| `mine` | industry | 1–12 | [mine.md](industry/mine.md) | [mine.json](../assets/specs/industry/mine.json) | есть | есть проектные поля |
| `clay_quarry` | industry | 1–12 | [clay-quarry.md](industry/clay-quarry.md) | [clay_quarry.yaml](../assets/specs/industry/clay_quarry.yaml) | есть | сверить числа |
| `iron_mine` | industry | 1 | [iron-mine.md](industry/iron-mine.md) | [iron_mine.json](../assets/specs/industry/iron_mine.json) | нет | есть проектные поля |
| `copper_mine` | industry | 1–10 | [copper-mine.md](industry/copper-mine.md) | [copper_mine.json](../assets/specs/industry/copper_mine.json) | есть | есть проектные поля |
| `resin_kiln` | industry | 1–10 | [resin-kiln.md](industry/resin-kiln.md) | [resin_kiln.json](../assets/specs/industry/resin_kiln.json) | есть | есть проектные поля |
| `sulfur_spring` | industry | 1–10 | [sulfur-spring.md](industry/sulfur-spring.md) | [sulfur_spring.json](../assets/specs/industry/sulfur_spring.json) | есть | есть проектные поля |
| `oil_well` | industry | 1–3 | [oil-well.md](resource-buildings/oil-well.md) | [oil_well.yaml](../assets/specs/industry/oil_well.yaml) | есть | модели и баланс уровней 1–3; два текстовых файла |
| `stone_cutters` | industry | 1 | [stone-cutters.md](industry/stone-cutters.md) | [stone_cutters.json](../assets/specs/industry/stone_cutters.json) | нет | есть проектные поля |
| `tile_factory` | industry | 1–10 | [tile-factory.md](industry/tile-factory.md) | [tile_factory.json](../assets/specs/industry/tile_factory.json) | есть | сверить числа |
| `cement_workshop` | industry | 1–10 | [cement-workshop.md](industry/cement-workshop.md) | [cement_workshop.json](../assets/specs/industry/cement_workshop.json) | есть | есть проектные поля |
| `concrete_plant` | industry | 1–10 | [concrete-plant.md](industry/concrete-plant.md) | [concrete_plant.json](../assets/specs/industry/concrete_plant.json) | есть | есть проектные поля |
| `rope_yard` | industry | 1–8 | [rope-yard.md](industry/rope-yard.md) | [rope_yard.json](../assets/specs/industry/rope_yard.json) | есть | сверить числа |
| `paper_workshop` | industry | 1–10 | [paper-workshop.md](industry/paper-workshop.md) | [paper_workshop.json](../assets/specs/industry/paper_workshop.json) | есть | есть проектные поля |
| `paint_workshop` | industry | 1–10 | [paint-workshop.md](industry/paint-workshop.md) | [paint_workshop.json](../assets/specs/industry/paint_workshop.json) | есть | есть проектные поля |
| `oil_press` | industry | 1–10 | [oil-press.md](industry/oil-press.md) | [oil_press.json](../assets/specs/industry/oil_press.json) | есть | есть проектные поля |
| `foundry` | industry | 1–10 | [foundry.md](industry/foundry.md) | [foundry.json](../assets/specs/industry/foundry.json) | есть | есть проектные поля |
| `steelworks` | industry | 1–10 | [steelworks.md](industry/steelworks.md) | [steelworks.json](../assets/specs/industry/steelworks.json) | есть | есть проектные поля |
| `electronics_workshop` | industry | 1–10 | [electronics-workshop.md](industry/electronics-workshop.md) | [electronics_workshop.json](../assets/specs/industry/electronics_workshop.json) | есть | есть проектные поля |
| `oil_refinery` | industry | 1–10 | [oil-refinery.md](industry/oil-refinery.md) | [oil_refinery.json](../assets/specs/industry/oil_refinery.json) | есть | есть проектные поля |
| `chemical_workshop` | industry | 1 | [chemical-workshop.md](industry/chemical-workshop.md) | [chemical_workshop.json](../assets/specs/industry/chemical_workshop.json) | нет | есть проектные поля |
| `military_factory` | industry | 1–10 | [military-factory.md](industry/military-factory.md) | [military_factory.json](../assets/specs/industry/military_factory.json) | есть | есть проектные поля |
| `precision_workshop` | industry | 1 | [precision-workshop.md](industry/precision-workshop.md) | [precision_workshop.json](../assets/specs/industry/precision_workshop.json) | нет | есть проектные поля |
| `siege_yard` | industry | 1–2 | [siege-yard.md](industry/siege-yard.md) | [siege_yard.json](../assets/specs/industry/siege_yard.json) | есть | модели уровней 1–2 и четырёх состояний подключены |
| `resonance_laboratory` | industry | 1 | [resonance-laboratory.md](industry/resonance-laboratory.md) | [resonance_laboratory.json](../assets/specs/industry/resonance_laboratory.json) | есть | производство резонансных зарядов и модель подключены |

## Неоднозначные соответствия и следующие проверки

- `road` → `ground-road.md` / `ground_road` в runtime; `standard_road` → `common-road.md` / `common_road`; `field_bed` → `windleaf-bed.md` / `windleaf_bed`; `lumber_yard` → `sawmill-yard.md`. Это алиасы имени файла/ассета, не дополнительные игровые ID.
- `oil_well` описан в `resource-buildings/oil-well.md` и `industry/oil-well.md`. Первый считать основным документом правил редкой клетки; второй — подробной модельной/промышленной спецификацией. Перед изменением баланса их нужно сверить между собой.
- `roads/reinforced-wall.md` описывает `reinforced_wall`, которого нет ни в backend, ни в shared-каталоге. Это концепт, а не доступная постройка. Активная ветка стен: `wooden_wall` 1–3 → `stone_wall` 4–7 → `concrete_wall` 8–10 → `modern_wall` 11–13.
- В каталоге башня `tower` имеет один уровень и не задаёт автоматическую атаку; защитники из двух баз ещё не созданы как отдельные сущности. Наличие спеки и модели не означает работу всех заявленных действий.
- Документы с «не задано» и «проектный баланс» требуют сверки по всем числовым полям. Список материальных конфликтов и решений ведётся в [аудите экономики](../game-design/economy-audit.md). Результат этой инвентаризации — основание для пунктов 21.3–21.14 основного плана.
