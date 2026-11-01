# Сверка игрового каталога построек

Отчёт сформирован `python3 docs/buildings/audit-catalogs.py`. Сравниваются ID, русское имя, категория, размер клетки, переходы апгрейда и **каждый игровой уровень**: время в секундах, строители, HP и стоимость по `resource_id`. Frontend импортирует generated `shared/catalog/buildings.ts`, а API `/api/v1/buildings/catalog` отдаёт runtime backend-каталог; оба используют `data/buildings/catalog-v2.json`. Текстовые документы и экранные описания требуют отдельной редакторской сверки.

| ID | Число уровней | Shared ↔ backend |
| --- | ---: | --- |
| `town_hall` | 10 | совпадает |
| `dugout` | 5 | совпадает |
| `wood_house` | 6 | совпадает |
| `stone_house` | 6 | совпадает |
| `apartment_house` | 1 | совпадает |
| `villa` | 5 | совпадает |
| `residential_skyscraper` | 1 | совпадает |
| `palace` | 1 | совпадает |
| `workshop` | 1 | совпадает |
| `brick_kiln` | 1 | совпадает |
| `brick_yard` | 10 | совпадает |
| `glass_workshop` | 12 | совпадает |
| `forge` | 1 | совпадает |
| `weaving_yard` | 10 | совпадает |
| `dye_works` | 1 | совпадает |
| `mechanical_workshop` | 10 | совпадает |
| `optical_workshop` | 1 | совпадает |
| `mint` | 1 | совпадает |
| `coin_storage` | 12 | совпадает |
| `market` | 1 | совпадает |
| `tower` | 1 | совпадает |
| `defense_cannon` | 12 | совпадает |
| `wooden_wall` | 3 | совпадает |
| `stone_wall` | 4 | совпадает |
| `concrete_wall` | 3 | совпадает |
| `modern_wall` | 3 | совпадает |
| `road` | 1 | совпадает |
| `standard_road` | 1 | совпадает |
| `paved_road` | 1 | совпадает |
| `alliance_house` | 1 | совпадает |
| `field_bed` | 11 | совпадает |
| `seed_garden` | 10 | совпадает |
| `herb_bed` | 9 | совпадает |
| `mushroom_grove` | 10 | совпадает |
| `flax_field` | 10 | совпадает |
| `reed_bed` | 10 | совпадает |
| `dye_garden` | 6 | совпадает |
| `oilseed_field` | 7 | совпадает |
| `sugar_bed` | 9 | совпадает |
| `crystal_greenhouse` | 4 | совпадает |
| `lumber_yard` | 13 | совпадает |
| `sand_quarry` | 11 | совпадает |
| `mine` | 12 | совпадает |
| `clay_quarry` | 12 | совпадает |
| `iron_mine` | 1 | совпадает |
| `copper_mine` | 10 | совпадает |
| `resin_kiln` | 10 | совпадает |
| `sulfur_spring` | 10 | совпадает |
| `oil_well` | 3 | совпадает |
| `stone_cutters` | 1 | совпадает |
| `tile_factory` | 10 | совпадает |
| `cement_workshop` | 10 | совпадает |
| `concrete_plant` | 10 | совпадает |
| `rope_yard` | 8 | совпадает |
| `paper_workshop` | 10 | совпадает |
| `paint_workshop` | 10 | совпадает |
| `oil_press` | 10 | совпадает |
| `foundry` | 10 | совпадает |
| `steelworks` | 10 | совпадает |
| `electronics_workshop` | 10 | совпадает |
| `oil_refinery` | 10 | совпадает |
| `chemical_workshop` | 1 | совпадает |
| `military_factory` | 10 | совпадает |
| `precision_workshop` | 1 | совпадает |
| `siege_yard` | 2 | совпадает |
| `resonance_laboratory` | 1 | совпадает |
| `defense_stakes` | 6 | совпадает |
| `defense_resin_snare` | 4 | совпадает |
| `defense_bolt_thrower` | 8 | совпадает |
| `defense_storm_coil` | 6 | совпадает |
| `defense_automaton_bay` | 5 | совпадает |
| `defense_guardian_enclosure` | 5 | совпадает |

Типов shared: **73**; backend: **73**; расхождений: **0**.

## Расхождения и решения

- Числовых расхождений между каталогами не найдено. Проектные поля текстовых документов не становятся игровыми автоматически.

## Оставшаяся редакторская проверка

- Сопоставить каждую числовую таблицу индивидуального документа с соответствующей строкой каталога. Особенно важны ранние дома, хранилище монет, ратуша, поля и проектные уровни позднего жилья.
- Сверить тексты карточек frontend: некоторые описания обещают выпуск у зданий без зарегистрированного серверного рецепта. До реализации рецепта показывать их как проектную роль.
- Проверить русские единицы: `buildSeconds` — секунды, `population` — строители, `FuelPerRun` — бензин на цикл; количество ресурса всегда целое.
