# Фактическое покрытие игровых ассетов

Сформировано `python3 docs/assets/scan-building-assets.py` по реестру 21.1 и файлам `frontend/public/assets/buildings/`. Это инвентаризация, а не визуальная приёмка или подтверждение подключения к рендереру. Тестовые и пилотные папки не учитываются. Значения уровней — только непустые файлы, на которые указывает production manifest. Для дорог без номера уровня в имени используется уровень каталога. Три набора после `LOD` соответствуют LOD0/1/2. `ruined` и стадии роста требуют дополнительной проверки по профильной спеке.

| Игровой ID | Уровни каталога | Спека | PNG active | PNG construction | PNG damaged | GLB LOD0/1/2 | `.blend` | report | Состояния manifest | lookup | Итог |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `town_hall` | 1–10 | да | — | — | — | — | — | — | — | да | нет manifest |
| `dugout` | 1–5 | да | — | — | — | — | — | — | — | да | нет manifest |
| `wood_house` | 1–6 | да | — | — | — | — | — | — | — | да | нет manifest |
| `stone_house` | 1–6 | да | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | —/—/— | да | да | active, construction, damaged | да | нужно: LOD |
| `apartment_house` | 4 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `villa` | 4 | да | 4 | — | — | 4/4/4 | нет | нет | active | да | нужно: construction, damaged, blend, report, лишние уровни 1, 2, 3, 5 |
| `palace` | 5 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `residential_skyscraper` | 5 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `workshop` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `brick_kiln` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `brick_yard` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `glass_workshop` | 1–9 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | —/—/— | да | да | active, construction, damaged, idle_no_input, idle_no_fuel, ready, ruined | да | нужно: LOD, лишние уровни 10, 11, 12 |
| `forge` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `weaving_yard` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `dye_works` | 1 | да | 1 | 1 | 1 | 1/1/1 | да | да | active, construction, damaged, ruined | да | готово |
| `mechanical_workshop` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `optical_workshop` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `mint` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `coin_storage` | 1–12 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | —/—/— | да | нет | active, construction, damaged, ruined | да | нужно: LOD, report |
| `market` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `tower` | 1 | да | 1 | 1 | 1 | 1/1/1 | да | да | construction, active, damaged | да | полно |
| `defense_cannon` | 1–12 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12/1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12/1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | да | да | active, construction, damaged, ruined | да | полно |
| `defense_stakes` | 1–6 | да | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6/1, 2, 3, 4, 5, 6/1, 2, 3, 4, 5, 6 | да | да | construction, armed, triggered, empty, damaged, ruined | да | полно |
| `defense_resin_snare` | 1–4 | да | 1, 2, 3, 4 | 1, 2, 3, 4 | 1, 2, 3, 4 | 1, 2, 3, 4/1, 2, 3, 4/1, 2, 3, 4 | да | да | construction, armed, triggered, empty, damaged, ruined | да | полно |
| `defense_bolt_thrower` | 1–8 | да | 1, 2, 3, 4, 5, 6, 7, 8 | 1, 2, 3, 4, 5, 6, 7, 8 | 1, 2, 3, 4, 5, 6, 7, 8 | 1, 2, 3, 4, 5, 6, 7, 8/1, 2, 3, 4, 5, 6, 7, 8/1, 2, 3, 4, 5, 6, 7, 8 | да | да | construction, active, no_crew, damaged, ruined | да | полно |
| `defense_storm_coil` | 1–6 | да | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6/1, 2, 3, 4, 5, 6/1, 2, 3, 4, 5, 6 | да | да | construction, active, no_fuel, no_crew, damaged, ruined | да | полно |
| `defense_automaton_bay` | 1–5 | да | 1, 2, 3, 4, 5 | 1, 2, 3, 4, 5 | 1, 2, 3, 4, 5 | 1, 2, 3, 4, 5/1, 2, 3, 4, 5/1, 2, 3, 4, 5 | да | да | construction, active, no_mechanic, no_fuel, damaged, ruined | да | полно |
| `defense_guardian_enclosure` | 1–5 | да | 1, 2, 3, 4, 5 | 1, 2, 3, 4, 5 | 1, 2, 3, 4, 5 | 1, 2, 3, 4, 5/1, 2, 3, 4, 5/1, 2, 3, 4, 5 | да | да | construction, active, no_keeper, damaged, ruined | да | полно |
| `wooden_wall` | 1–3 | да | — | — | — | — | — | — | — | да | нет manifest |
| `stone_wall` | 4–7 | да | — | — | — | — | — | — | — | да | нет manifest |
| `concrete_wall` | 8–10 | да | — | — | — | — | — | — | — | да | нет manifest |
| `modern_wall` | 11–13 | да | — | — | — | — | — | — | — | да | нет manifest |
| `road` | 1 | да | 1 | 1 | 1 | —/—/— | да | нет | active, construction, damaged, ruined | да | нужно: LOD, report |
| `standard_road` | 2 | да | 2 | 2 | 2 | —/—/— | да | нет | active, construction, damaged, ruined | да | нужно: LOD, report, лишние уровни 1 |
| `paved_road` | 3 | да | 3 | 3 | 3 | —/—/— | да | нет | active, construction, damaged, ruined | да | нужно: LOD, report, лишние уровни 1 |
| `alliance_house` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `field_bed` | 1–11 | да | — | — | — | —/—/— | да | да | — | да | нужно: active, construction, damaged, LOD |
| `seed_garden` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | —/—/— | да | да | stage01, stage02, stage03, active, construction, damaged, ruined, super_stage01, super_stage02, super_stage03, super_stage04, super_stage05, super_stage06 | да | нужно: LOD |
| `herb_bed` | 1–9 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 1, 2, 3, 4, 5, 6, 7, 8, 9 | —/—/— | да | да | stage01, stage02, stage03, active, construction, damaged, ruined, super_stage01, super_stage02, super_stage03, super_stage04, super_stage05, super_stage06 | да | нужно: LOD |
| `mushroom_grove` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | —/—/— | да | да | stage01, stage02, stage03, active, construction, damaged, ruined, super_stage01, super_stage02, super_stage03, super_stage04, super_stage05, super_stage06 | да | нужно: LOD |
| `flax_field` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | —/—/— | да | да | stage01, stage02, stage03, active, construction, damaged, ruined, super_stage01, super_stage02, super_stage03, super_stage04, super_stage05, super_stage06 | да | нужно: LOD |
| `reed_bed` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | —/—/— | да | да | stage01, stage02, stage03, active, construction, damaged, ruined, super_stage01, super_stage02, super_stage03, super_stage04, super_stage05, super_stage06 | да | нужно: LOD |
| `dye_garden` | 1–6 | да | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6 | 1, 2, 3, 4, 5, 6/1, 2, 3, 4, 5, 6/1, 2, 3, 4, 5, 6 | да | да | construction, stage01, stage02, stage03, stage04, active, damaged, ruined | да | полно |
| `oilseed_field` | 1–7 | да | 1, 2, 3, 4, 5, 6, 7 | 1, 2, 3, 4, 5, 6, 7 | 1, 2, 3, 4, 5, 6, 7 | —/—/— | да | да | stage01, stage02, stage03, active, construction, damaged, ruined, super_stage01, super_stage02, super_stage03, super_stage04, super_stage05, super_stage06 | да | нужно: LOD |
| `sugar_bed` | 1–9 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `crystal_greenhouse` | 1–4 | да | 1, 2, 3, 4 | 1, 2, 3, 4 | 1, 2, 3, 4 | 1, 2, 3, 4/1, 2, 3, 4/1, 2, 3, 4 | да | да | construction, stage01, stage02, stage03, stage04, active, damaged, ruined | да | полно |
| `lumber_yard` | 1–13 | да | — | — | — | — | — | — | — | да | нет manifest |
| `sand_quarry` | 1–11 | да | — | — | — | —/—/— | да | да | active, construction, damaged | да | нужно: active, construction, damaged, LOD |
| `mine` | 1–12 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | —/—/— | да | да | active, construction, damaged | да | нужно: LOD |
| `clay_quarry` | 1–12 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | —/—/— | да | да | active, construction, damaged | да | нужно: LOD |
| `iron_mine` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `copper_mine` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `resin_kiln` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `sulfur_spring` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `oil_well` | 1 | да | — | — | — | —/—/— | да | да | active, construction, damaged, ruined | да | нужно: active, construction, damaged, LOD, лишние уровни 2, 3 |
| `stone_cutters` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `tile_factory` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `cement_workshop` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `concrete_plant` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `rope_yard` | 1–8 | да | 1, 2, 3, 4, 5, 6, 7, 8 | 1, 2, 3, 4, 5, 6, 7, 8 | 1, 2, 3, 4, 5, 6, 7, 8 | —/—/— | да | да | active, ready, idle_no_input, idle_no_workers, construction, damaged, ruined | да | нужно: LOD |
| `paper_workshop` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `paint_workshop` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `oil_press` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `foundry` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `steelworks` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `electronics_workshop` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `oil_refinery` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `chemical_workshop` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |
| `military_factory` | 1–10 | да | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10/1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | да | да | active, construction, damaged | да | полно |
| `precision_workshop` | 1 | да | — | — | — | — | — | — | — | нет | нет manifest |

Проверено типов: **71**; с неполным набором или без production manifest: **44**.

## Перед передачей в production

- Для каждой обязательной пары `building_id × level × state` сверить geometry, alpha, footprint, anchor, материалы и три LOD по [визуальному контракту](building-asset-contract.md).
- `lookup` означает наличие `kind` в `buildingAssetManifests.ts`; карту и 3D-просмотр дополнительно проверить сценарием, поскольку статическая запись ещё не доказывает успешную загрузку.
- Для полей дополнительно проверить стадии роста и супер-версию; для дорог и стен — формы стыков; для разрушимых объектов — `ruined` либо утверждённый fallback.
- Удалять или переносить тестовые варианты только после принятия production-семейства и проверки ссылок.
