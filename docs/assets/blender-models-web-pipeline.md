# Пайплайн Blender-Моделей Для Веб-Карты

## Назначение

Пайплайн создает fantasy mid-poly ассеты Real City для изометрической веб-карты. Blender хранит мастер-сцену и GLB, а основной runtime карты использует PNG-спрайты с прозрачным фоном, единым масштабом и стабильным anchor.

Целевой стиль: `aeolian_fantasy_midpoly` из `docs/art/visual-style-guide.md`: яркая читаемая фентезийная диорама, оптимизированная геометрия, hand-painted-like материалы, умеренные эолийские акценты и отсутствие low-poly-заглушечного вида.

## Архитектура

| Слой | Файлы | Роль |
| --- | --- | --- |
| Asset spec | `docs/assets/specs/**/*.yaml` | Короткий источник требований: `asset_id`, category, footprint, levels, states, material map, progression, style/skill profile, LOD и PNG policy |
| Общий Blender API | `tools/assets/blender/real_city/` | Сцена, камера, свет, материалы, геометрия, ground, state/export/report helpers, validation helpers |
| Component library | `tools/assets/blender/real_city/components/` | Переиспользуемые стены, крыши, двери, окна, фундаменты, башни, props, грядки, industry-детали и detail kits |
| Orchestrator | `tools/assets/generate_blender_asset.py`, `tools/assets/blender/real_city/orchestrator.py` | `asset_id/spec -> temporary Blender script -> preview/full/repair -> reports/status` |
| Runtime assets | `frontend/public/assets/buildings/<category>/<asset_id>/` | PNG, LOD GLB, `.blend`, `manifest.json`, `generation-report.json`, contact sheets |
| Frontend lookup | `frontend/src/game/renderers/buildingAssetManifests.ts`, `buildingRegistry.ts` | Manifest-driven выбор PNG/GLB по `building.kind`, level, state и shape |

Новые ассеты по умолчанию кладутся в `frontend/public/assets/buildings/...`. Legacy-семейства, которые уже подключены из `frontend/src/assets`, поддерживаются registry-слоем для совместимости, но новый стандарт хранения - `public/assets`.

## Output Contract

Минимальный выход для каждого `level/state`:

```text
<asset_id>_l03_active.png
<asset_id>_l03_active_LOD0.glb
<asset_id>_l03_active_LOD1.glb
<asset_id>_l03_active_LOD2.glb
```

Для shape-based дорог и стен вместо уровня используется shape:

```text
<asset_id>_straight_ew_active.png
<asset_id>_straight_ew_active_LOD0.glb
```

Папка ассета должна содержать:

- `.blend` мастер-сцену или мастер-сцену партии;
- runtime PNG;
- runtime GLB LOD0/LOD1/LOD2, если ассет не является PNG-only исключением;
- `manifest.json`;
- `generation-report.json`;
- contact sheet для preview/full партии;
- при возможности `roundtrip-validation.json`.

## PNG Runtime Policy

- building PNG: `512x384`, прозрачный фон, anchor `[256, 292]`;
- ground/road/wall shape PNG может использовать отдельный размер, если это закреплено manifest и frontend lookup;
- камера, ортографический масштаб, свет и view transform должны быть едиными внутри семейства;
- ground-клетка active/construction/damaged одного уровня не меняет геометрию, положение, материал и UV;
- проверка читаемости идет в полном кадре и после уменьшения примерно до `128x96`.

## LOD Policy

| Тип ассета | LOD0 | LOD1 | LOD2 | Runtime PNG |
| --- | ---: | ---: | ---: | --- |
| Малый prop, ресурс, пень | 300-900 tris | 150-450 tris | 80-200 tris | Рендер из LOD0 |
| 1x1 раннее здание | 1 500-3 500 tris | 700-1 800 tris | 300-800 tris | Рендер из LOD0 |
| 1x1 развитое здание | 3 000-6 000 tris | 1 200-3 000 tris | 600-1 300 tris | Рендер из LOD0 |
| 2x2 civic/market/landmark | 6 000-12 000 tris | 2 500-6 000 tris | 1 000-2 500 tris | Рендер из LOD0 |

LOD1/LOD2 обязаны сохранять основной силуэт, вход, крышу, footprint и главные props. Мелкую детализацию можно переносить в материалы, фаски и текстурные акценты.

## Skill Profile

Spec хранит компактный `skill_profile`, а не длинный prompt. Базовый профиль для building assets:

- base: `blender-director`, `genre-strategy-sim`, `isometric-style`, `fantasy-worlds`, `stylized-style`, `hand-painted-style`;
- asset type: `environment-artist`, `prop-artist`, `hard-surface`, `vegetation-artist`, `creature-artist` или `vehicle-artist`;
- production: `materials`, `texture-workflow`, `lookdev`, `lod-pipeline`, `asset-optimization`, `collision-proxy`, `export-pipeline`;
- validation: `qa-review`.

Профиль нужен как короткий набор правил принятия решений: силуэт, детализация, материалы, budgets, LOD и quality gates. Фактическая генерация идет через spec, общий API и reusable components.

## Рабочий Маршрут

1. Найти или создать spec в `docs/assets/specs/`.
2. Прочитать только релевантные источники: spec, нужный `docs/buildings/**`, `docs/art/visual-style-guide.md`, текущий `docs/assets/asset-generation-status.md` и короткие skill-файлы.
3. Выполнить dry-run:

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode dry-run
```

4. Сгенерировать preview контрольных уровней:

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode preview
```

5. Проверить contact sheet, PNG alpha/bounds, manifest, LOD budgets и style checklist.
6. Запустить full только после успешного preview или с явным override:

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode full
```

7. При локальной правке использовать repair-режим вместо полной регенерации:

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target png
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target lod
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target manifest
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target contact-sheet
```

8. Обновить frontend registry, если добавлено новое семейство.
9. Обновить `docs/assets/asset-generation-status.md` короткой записью: что создано, где лежит, какие проверки прошли, какие ограничения остались.

## Проверки

Быстрая проверка без тяжелого Blender-рендера:

```bash
make asset-pipeline-smoke
```

Contact sheets:

```bash
make asset-contact-sheets
```

Полная локальная проверка на машине с Blender:

```bash
make asset-pipeline-local
```

Точечные валидаторы:

```bash
python3 tools/assets/validate_asset_specs.py
python3 tools/assets/validate_building_manifests.py
python3 tools/assets/validate_building_sprites.py
python3 tools/assets/validate_building_lods.py
python3 tools/assets/blender/validate_glb_roundtrip.py <asset-folder>
```

## Интеграция Во Frontend

Runtime lookup идет через `buildingRegistry.ts`:

- level clamp берется из compact manifest metadata;
- state policy учитывает только модельные состояния `active`, `construction`, `damaged`; planned/building мапятся на `construction`, критический урон и руины мапятся на `damaged`, а производственные и UI-статусы отображаются overlay/анимацией поверх `active`;
- public assets строятся как `/assets/buildings/<category>/<asset_id>/<file>`;
- legacy `src/assets` модели подключаются через `import.meta.glob`;
- roads/walls используют shape lookup.

Dev-панель ассетов включается в режиме разработки через:

```text
http://localhost:5173/?assets=1
```

Панель показывает зарегистрированные семейства, levels/states, PNG/GLB preview и локальные ошибки lookup.

## Token-Budget Policy

- Не копировать длинный art guide или skill instructions в prompts и чат.
- Держать повторяемые решения в spec, API, components и валидаторах.
- Большие Blender-логи хранить в `/tmp` или рядом с ассетной партией.
- В чат выводить только итог: файлы, counts, contact sheet, PASS/FAIL и ограничения.
- Для продолжения после паузы читать `docs/assets/asset-generation-status.md`, а не всю историю переписки.
