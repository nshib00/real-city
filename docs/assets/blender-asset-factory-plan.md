# Real City Blender Asset Factory — План реализации

Пунктов плана выполнено: 72/72 (100%)

## Подход к логированию

Пайплайн генерации 3D-моделей должен оставлять короткий машинно-читаемый след для каждой партии ассетов: входная спецификация, версия генератора, список созданных файлов, triangle count, bounds, sprite size, anchor, результаты проверок и путь к contact sheet. Подробные Blender-логи остаются в `/tmp` или рядом с ассетной партией, а в `docs/assets/asset-generation-status.md` фиксируется только итог, ограничения и следующий шаг.

Планируемая модель:

- Codex orchestration log: `asset_id`, уровни, состояния, выбранные референсные семейства, путь к spec, команды MCP, путь к Blender log.
- Blender generation report: `generator_version`, `source_spec`, `source_blend`, `combined_glb`, runtime GLB/PNG, triangles, bounds, materials, sprite metadata.
- Validation report: ground signatures, topology/roundtrip, non-empty PNG alpha bounds, manifest completeness, contact sheet path.
- Status memory: после крупных партий обновлять `docs/assets/asset-generation-status.md`, не переносить длинные логи в чат.
- Ошибки: разделять `mcp_unavailable`, `generation_failed`, `export_failed`, `visual_review_failed`, `validation_failed`, чтобы Codex мог продолжать с правильной точки.

## Целевая модель fantasy mid-poly pipeline

Целевая фабрика должна создавать ассеты в стиле `Aeolian bright fantasy mid-poly strategy diorama` из `docs/art/visual-style-guide.md`: яркая фентезийная изометрическая диорама, читаемая на стратегической карте, с оптимизированной mid-poly геометрией, hand-painted-like материалами, контролируемыми эолийскими мотивами и обязательными PNG-рендерами для runtime.

Основной runtime-формат карты остается PNG-спрайтом с прозрачным фоном, единым якорем и фиксированной изометрической камерой. `.blend` и `.glb` сохраняются как мастер-ассеты, источник рендера, материал для инспекции, будущего 3D-превью и контроля качества. Для GLB-пакета нужно готовить LOD-цепочку, даже если текущий frontend использует PNG.

Рекомендуемый профиль Blender-skills для новых зданий и map-assets:

- Базовый профиль: `blender-director`, `genre-strategy-sim`, `isometric-style`, `fantasy-worlds`, `stylized-style`, `hand-painted-style`.
- По типу ассета: `environment-artist`, `prop-artist`, `hard-surface`, `vegetation-artist`, `creature-artist` или `vehicle-artist`.
- Производство: `materials`, `texture-workflow`, `lookdev`, `lod-pipeline`, `asset-optimization`, `collision-proxy`, `export-pipeline`, `qa-review`.

Skill-профиль не должен превращаться в длинный свободный prompt. Он нужен как компактный набор правил принятия решений: какой силуэт выбрать, какие детали оставить в геометрии, что унести в текстуры, какие бюджеты проверить и какие quality gates выполнить. Фактическая генерация должна идти через asset spec, общий Blender API, reusable components и валидаторы.

Экономия токенов строится на четырех правилах:

- Asset spec коротко описывает `asset_id`, category, footprint, levels, states, budgets, style profile, LOD policy, PNG policy и ключевые мотивы вместо повторения полного арт-гайда.
- Codex читает только релевантные документы: spec, нужный `docs/buildings/**`, `docs/art/visual-style-guide.md`, текущий manifest/status и выбранные короткие skill-файлы.
- Большие Blender scripts, логи и отчеты не переносятся в чат; в чат попадает только итог: файлы, triangle counts, contact sheet, PASS/FAIL и ограничения.
- Повторяемые решения живут в коде: палитра, камера, render profile, LOD ratios, naming, output folders, validation thresholds.

LOD-политика:

| Тип ассета | LOD0 | LOD1 | LOD2 | Runtime PNG |
|---|---:|---:|---:|---|
| Малый prop, ресурс, пень | 300-900 tris | 150-450 tris | 80-200 tris | Рендер из LOD0 |
| 1x1 раннее здание | 1 500-3 500 tris | 700-1 800 tris | 300-800 tris | Рендер из LOD0 |
| 1x1 развитое здание | 3 000-6 000 tris | 1 200-3 000 tris | 600-1 300 tris | Рендер из LOD0 |
| 2x2 civic/market/landmark | 6 000-12 000 tris | 2 500-6 000 tris | 1 000-2 500 tris | Рендер из LOD0 |

Минимальный выход на каждый `level/state`:

```text
<asset_id>_l03_active.png
<asset_id>_l03_active_LOD0.glb
<asset_id>_l03_active_LOD1.glb
<asset_id>_l03_active_LOD2.glb
```

Для building sprites по умолчанию использовать `512x384`, прозрачный фон, общий anchor `[256, 292]`, contact sheet для preview/full партий и alpha/bounds validation.

## Фаза 1 — Единый Blender API

Цель фазы: вынести повторяющиеся правила сцены, материалов, геометрии, ground-клетки, состояний и экспорта из отдельных генераторов в общий Python API, пригодный для вызова через Blender MCP и постепенной миграции текущих скриптов.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 1.1 | Пакет общего API с явной точкой импорта и без обязательного `bpy` при обычной Python-компиляции | `tools/assets/blender/real_city/__init__.py` | ✅ |
| 1.2 | Константы runtime-рендера: sprite size, anchor, tile size, ground width, состояния, категории отчетов | `tools/assets/blender/real_city/constants.py` | ✅ |
| 1.3 | Утилиты путей для WSL/Windows Blender: корень проекта, runtime folders, UNC-преобразование для MCP | `tools/assets/blender/real_city/paths.py` | ✅ |
| 1.4 | Scene API: очистка сцены, единая изометрическая камера, свет, render settings, прозрачный PNG, world/view transform | `tools/assets/blender/real_city/scene.py` | ✅ |
| 1.5 | Material API: единая палитра Real City, создание Principled BSDF через node type, alpha/emission/roughness/metallic | `tools/assets/blender/real_city/materials.py` | ✅ |
| 1.6 | Geometry API: коллекции, mesh primitives, bevel boxes, beams, roofs, flags, transforms, stats/bounds | `tools/assets/blender/real_city/geometry.py` | ✅ |
| 1.7 | Ground API: единая flat ground-клетка и дорожка с именами, совместимыми с ground validators | `tools/assets/blender/real_city/ground.py` | ✅ |
| 1.8 | Export/state/validation API: show/select collections, `.blend`, `.glb`, PNG render, manifest/report helpers, GLB header check | `tools/assets/blender/real_city/state.py`, `tools/assets/blender/real_city/export.py`, `tools/assets/blender/real_city/validation.py` | ✅ |
| 1.9 | Документация API: публичные модули, пример генератора, правила миграции старых скриптов | `tools/assets/blender/real_city/README.md` | ✅ |
| 1.10 | Smoke-проверка без Blender: `py_compile` всех модулей общего API | `tools/assets/blender/real_city/*.py` | ✅ |

---

## Фаза 2 — Asset Spec Format

| # | Что | Файлы | Статус |
|---|---|---|---|
| 2.1 | JSON Schema/YAML-структура спецификации ассета: `asset_id`, category, levels, states, footprint, output, references | `docs/assets/specs/schema.json`, `tools/assets/specs/` | ✅ |
| 2.2 | Поле material map: ресурс из стоимости -> видимая деталь модели, обязательное для построек | `docs/assets/specs/schema.json` | ✅ |
| 2.3 | Level progression DSL: правила роста массы, материалов, props, высоты, поздних элементов и ограничений | `docs/assets/specs/schema.json`, `tools/assets/blender/real_city/spec.py` | ✅ |
| 2.4 | State policy: только active/construction/damaged; planned/building мапятся на construction, ruined/critical damage - на damaged, production/UI statuses - overlay поверх active | `tools/assets/blender/real_city/spec.py` | ✅ |
| 2.5 | Валидатор спецификаций против `shared/catalog/buildings.ts` и `docs/buildings/**/*.md` | `tools/assets/validate_asset_specs.py` | ✅ |
| 2.6 | Эталонные specs для `dugout`, `wood_house`, `town_hall` на основе удачных текущих моделей | `docs/assets/specs/housing/`, `docs/assets/specs/center/` | ✅ |
| 2.7 | Spec template для новых зданий с комментариями на русском | `docs/assets/specs/template.yaml` | ✅ |
| 2.8 | Поле `style_profile` с базовым значением `aeolian_fantasy_midpoly`, чтобы spec ссылался на арт-гайд вместо копирования длинного описания | `docs/assets/specs/schema.json`, `tools/assets/blender/real_city/spec.py` | ✅ |
| 2.9 | Поле `skill_profile`: компактный список Blender-skills для ассета, разделенный на базовый профиль, тип ассета, production и validation | `docs/assets/specs/schema.json`, `docs/assets/specs/template.yaml` | ✅ |
| 2.10 | Поле `lod_policy`: LOD0/LOD1/LOD2 budgets, triangle ratios, naming, export flags и правила сохранения силуэта | `docs/assets/specs/schema.json`, `tools/assets/blender/real_city/spec.py` | ✅ |
| 2.11 | Поле `png_policy`: sprite size, camera profile, transparent background, anchor, contact sheet layout и alpha/bounds thresholds | `docs/assets/specs/schema.json`, `tools/assets/blender/real_city/spec.py` | ✅ |

---

## Фаза 3 — Библиотека Переиспользуемых Ассетов

| # | Что | Файлы | Статус |
|---|---|---|---|
| 3.1 | Разобрать удачные модели ратуш, землянок и домов на reusable-компоненты: крыши, окна, двери, фундаменты, props | `tools/assets/blender/real_city/components/` | ✅ |
| 3.2 | Parametric factories для жилых зданий: ранняя земля/дерево, фасады, входы, крыши, дворы | `tools/assets/blender/real_city/components/housing.py` | ✅ |
| 3.3 | Parametric factories для civic/center: башни, флаги, площади, балконы, поздние каменные/кирпичные элементы | `tools/assets/blender/real_city/components/civic.py` | ✅ |
| 3.4 | Parametric factories для production/industry: печи, станки, склады сырья, навесы, трубы, индикаторы готовности | `tools/assets/blender/real_city/components/industry.py` | ✅ |
| 3.5 | Prop kit: ящики, бочки, мешки, штабели досок, инструменты, верстаки, обломки, строительные леса | `tools/assets/blender/real_city/components/props.py` | ✅ |
| 3.6 | Aeolian kit: флюгеры, ленты, мягко изогнутые навесы, редкие кристаллы, световые линзы | `tools/assets/blender/real_city/components/aeolian.py` | ✅ |
| 3.7 | Source `.blend` library для сложных reusable collections, если Python factory недостаточен | `tools/assets/blender/library/README.md`, `tools/assets/blender/real_city/components/registry.py` | ✅ |
| 3.8 | Правила версионирования reusable-компонентов, чтобы старые ассеты не менялись неожиданно | `tools/assets/blender/real_city/components/README.md` | ✅ |
| 3.9 | Mid-poly detail kits: фасадные накладки, скосы, крупные повреждения, readable props и texture-bake-friendly детали, чтобы повышать качество без ручного переписывания генераторов | `tools/assets/blender/real_city/components/detail_kits.py` | ✅ |

---

## Фаза 4 — Codex + Blender MCP Orchestrator

| # | Что | Файлы | Статус |
|---|---|---|---|
| 4.1 | CLI-оркестратор `asset_id -> spec -> Blender MCP script -> preview/full generation` | `tools/assets/generate_blender_asset.py` | ✅ |
| 4.2 | Режим `preview`: генерировать уровни `1/middle/max` и contact sheet до полной партии | `tools/assets/generate_blender_asset.py` | ✅ |
| 4.3 | Режим `full`: вся линейка уровней и состояний только после успешного preview или явного флага | `tools/assets/generate_blender_asset.py` | ✅ |
| 4.4 | MCP bootstrap: проверка Blender addon status, scene info, Windows host `172.28.192.1`, лог ошибок подключения | `tools/assets/blender_mcp_bootstrap.py` | ✅ |
| 4.5 | Генерация temporary Blender script из spec без ручного копирования больших блоков в чат | `tools/assets/blender/real_city/orchestrator.py` | ✅ |
| 4.6 | Автоматическое обновление `docs/assets/asset-generation-status.md` после успешной партии | `tools/assets/update_asset_generation_status.py` | ✅ |
| 4.7 | Команда dry-run: показать, какие docs/catalog/spec/files будут затронуты | `tools/assets/generate_blender_asset.py` | ✅ |
| 4.8 | Skill execution brief: из spec и выбранных Blender-skills генерировать короткий машинный production brief без длинного prompt в чат | `tools/assets/blender/real_city/orchestrator.py` | ✅ |
| 4.9 | Режим `repair`: пересобрать только PNG, только LOD, только manifest/report или только contact sheet без полной регенерации ассета | `tools/assets/generate_blender_asset.py` | ✅ |
| 4.10 | Preview approval gate: `full` запуск требует успешного preview или явного флага, чтобы не тратить Blender-время и токены на плохую полную партию | `tools/assets/generate_blender_asset.py`, `docs/assets/asset-generation-status.md` | ✅ |
| 4.11 | Token-budget policy: оркестратор фиксирует, какие документы и skill-файлы были прочитаны, а длинные логи оставляет в файлах | `tools/assets/generate_blender_asset.py`, `docs/assets/asset-generation-status.md` | ✅ |
| 4.12 | Единый output contract для `.blend`, combined GLB, per-state LOD GLB, PNG, manifest, report и contact sheet | `tools/assets/blender/real_city/export.py`, `tools/assets/blender/real_city/orchestrator.py` | ✅ |

---

## Фаза 5 — Миграция Текущих Генераторов

| # | Что | Файлы | Статус |
|---|---|---|---|
| 5.1 | Мигрировать `dugout` на общий API без изменения визуального результата | `tools/assets/blender/generate_dugout_models.py`, `tools/assets/blender/real_city/migration.py` | ✅ |
| 5.2 | Мигрировать `wood_house` и сохранить уровни 1-6, состояния, scale/anchor | `tools/assets/blender/generate_wood_house_models.py`, `tools/assets/blender/real_city/migration.py` | ✅ |
| 5.3 | Мигрировать `town_hall` как эталон 2x2 civic chain | `tools/assets/blender/regenerate_town_halls.py`, `tools/assets/blender/real_city/migration.py` | ✅ |
| 5.4 | Мигрировать `lumber_yard`, проверить public-assets схему и ground validator | `tools/assets/blender/regenerate_sawmills.py`, `tools/assets/blender/real_city/migration.py` | ✅ |
| 5.5 | Мигрировать `glass_workshop`, `mine`, `sand_quarry`, `coin_storage` на общий scene/export/report слой | `tools/assets/blender/generate_*_models.py`, `tools/assets/blender/real_city/migration.py` | ✅ |
| 5.6 | Убрать локальные дубли `setup_camera`, `palette`, `export_one`, `write_manifest`, если генератор уже перешел на API | `tools/assets/blender/real_city/migration.py`, `tools/assets/blender/real_city/export.py` | ✅ |
| 5.7 | Зафиксировать compatibility fixtures: до/после bounds, sprite anchor, triangle ranges | `tools/assets/tests/fixtures/`, `tools/assets/blender/real_city/migration.py` | ✅ |

---

## Фаза 6 — Валидация и Quality Gates

| # | Что | Файлы | Статус |
|---|---|---|---|
| 6.1 | Обобщить ground validation для всех public/src families, не только захардкоженного списка | `tools/assets/validate_building_ground.py`, `tools/assets/asset_validation_common.py` | ✅ |
| 6.2 | Единый validator manifest completeness: все уровни/состояния имеют PNG, GLB, metadata | `tools/assets/validate_building_manifests.py` | ✅ |
| 6.3 | Roundtrip GLB import через Blender для новых партий | `tools/assets/blender/real_city/validation.py`, `tools/assets/blender/validate_glb_roundtrip.py` | ✅ |
| 6.4 | Contact sheet generator для preview/full партий с одинаковой раскладкой | `tools/assets/make_asset_contact_sheet.py` | ✅ |
| 6.5 | Pixel/alpha проверки PNG: размер, непустота, bounds внутри кадра, нижняя грань anchor | `tools/assets/validate_building_sprites.py` | ✅ |
| 6.6 | Material-map validation: ресурсы стоимости реально отражены в generation report | `tools/assets/validate_asset_specs.py` | ✅ |
| 6.7 | CI target для asset pipeline smoke без тяжелого рендера | `Makefile` | ✅ |
| 6.8 | Полный local target для Blender-enabled машины | `Makefile`, `tools/assets/blender/validate_glb_roundtrip.py` | ✅ |
| 6.9 | LOD validation: проверить наличие LOD0/LOD1/LOD2, triangle budgets, naming, bounds consistency и сохранение основного силуэта | `tools/assets/validate_building_lods.py`, `tools/assets/blender/real_city/validation.py` | ✅ |
| 6.10 | Style validation checklist: подтвердить `aeolian_fantasy_midpoly`, читаемый footprint, изометрическую читаемость, отсутствие low-poly-заглушечного вида и неконтролируемого grimdark | `docs/assets/blender-generation-checklist.md`, `tools/assets/validate_asset_specs.py` | ✅ |
| 6.11 | PNG runtime validation: contact sheet, alpha bounds, anchor, sprite size, отсутствие пустого прозрачного рендера и проверка small-scale читаемости | `tools/assets/validate_building_sprites.py`, `tools/assets/make_asset_contact_sheet.py` | ✅ |

---

## Фаза 7 — Frontend Runtime Integration

| # | Что | Файлы | Статус |
|---|---|---|---|
| 7.1 | Унифицировать выбор ассетов: manifest-driven lookup вместо ручного подключения каждого здания | `frontend/src/game/renderers/buildingAssetManifests.ts`, `frontend/src/game/renderers/buildingSpriteAssets.ts`, `frontend/src/game/renderers/buildingModelAssets.ts` | ✅ |
| 7.2 | Поддержать public/src assets единым способом или принять один стандарт хранения для новых моделей | `docs/frontend/rendering-and-assets.md`, `frontend/src/game/renderers/buildingRegistry.ts` | ✅ |
| 7.3 | Добавить renderer registry по `building.kind`, category, level/state policy | `frontend/src/game/renderers/buildingRegistry.ts` | ✅ |
| 7.4 | Тесты lookup: clamped levels, construction, damaged по HP threshold, ruined -> damaged fallback, UI/production statuses -> active overlay | `frontend/src/game/renderers/buildingRegistry.test.ts`, `frontend/src/game/renderers/buildingSpriteAssets.test.ts`, `frontend/src/game/renderers/buildingModelAssets.test.ts` | ✅ |
| 7.5 | Dev/debug экран ассетов: список семейств, levels/states, PNG/GLB preview, manifest errors | `frontend/src/features/assets/AssetDebugPanel.tsx`, `frontend/src/features/assets/AssetDebugPanel.test.ts` | ✅ |

---

## Фаза 8 — Документация и Рабочий Процесс

| # | Что | Файлы | Статус |
|---|---|---|---|
| 8.1 | Обновить `docs/assets/blender-models-web-pipeline.md` под новую factory-архитектуру | `docs/assets/blender-models-web-pipeline.md` | ✅ |
| 8.2 | Обновить skill `skills/real-city-blender-models/SKILL.md`: сначала spec/API/orchestrator, затем MCP | `skills/real-city-blender-models/SKILL.md` | ✅ |
| 8.3 | Добавить checklist для Codex: какие файлы читать, какой preview делать, какие проверки запускать | `docs/assets/blender-generation-checklist.md` | ✅ |
| 8.4 | Описать troubleshooting WSL/Windows Blender paths и `172.28.192.1` | `docs/assets/blender-mcp-troubleshooting.md` | ✅ |
| 8.5 | Описать правила обновления `asset-generation-status.md` и хранения больших логов | `docs/assets/asset-generation-status.md` | ✅ |
| 8.6 | Описать профиль `aeolian_fantasy_midpoly`: рекомендуемые Blender-skills, token-budget policy, LOD policy, PNG policy и минимальный output contract | `docs/assets/blender-models-web-pipeline.md` | ✅ |
| 8.7 | Добавить короткие рецепты генерации: новое здание, ресурсный prop, руина, vegetation tile, пересборка только PNG, пересборка только LOD | `docs/assets/blender-generation-checklist.md` | ✅ |

---

## Порядок зависимостей

```text
Фаза 1 Единый Blender API
  -> Фаза 2 Asset Spec Format
    -> Фаза 3 Библиотека переиспользуемых ассетов
      -> Фаза 4 Codex + Blender MCP Orchestrator
        -> Фаза 5 Миграция текущих генераторов
          -> Фаза 6 Валидация и Quality Gates
            -> Фаза 7 Frontend Runtime Integration
              -> Фаза 8 Документация и рабочий процесс
```
