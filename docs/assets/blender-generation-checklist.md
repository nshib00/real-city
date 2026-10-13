# Чеклист Blender-Генерации

Чеклист используется перед preview/full запуском и перед финальным ответом по ассету. Автоматические валидаторы проверяют структуру файлов, но художественное качество и соответствие сеттингу нужно подтвердить вручную по contact sheet или viewport screenshot.

## Что Читать Перед Работой

- `docs/assets/asset-generation-status.md` - текущие партии, ограничения, последние проблемы.
- `docs/assets/specs/<category>/<asset_id>.yaml` или `docs/assets/specs/template.yaml`.
- Релевантный файл из `docs/buildings/**`.
- `docs/art/visual-style-guide.md`.
- `skills/real-city-blender-models/SKILL.md` и только нужные references из `skills/real-city-blender-models/references/`.
- Для frontend-подключения: `docs/frontend/rendering-and-assets.md`, `frontend/src/game/renderers/buildingAssetManifests.ts`, `frontend/src/game/renderers/buildingRegistry.ts`.

## Перед Генерацией

- Spec содержит `asset_id`, `category`, `levels`, `states`, `footprint`, `material_map`, `level_progression`, `state_policy`, `style_profile`, `skill_profile`, `lod_policy`, `png_policy`.
- `style_profile` равен `aeolian_fantasy_midpoly`.
- `material_map` связывает ресурсы стоимости с видимыми деталями модели.
- LOD budgets соответствуют типу ассета.
- PNG policy задает размер, камеру, прозрачный фон, anchor и alpha/bounds thresholds.
- Для Blender MCP учтен WSL/Windows host `172.28.192.1`.

## Preview Gate

Запусти preview для контрольных уровней `1/middle/max`:

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode preview
```

Проверь:

- создана contact sheet;
- уровни отличаются формой, объемом и материалами, а не только размером или цветом;
- active/construction/damaged читаются как разные состояния;
- construction показывает недостроенную геометрию с отсутствующими частями стен/крыши;
- damaged имеет крупные реальные разрушения; если серверное состояние требует руины, runtime использует damaged как визуальный fallback;
- детали не левитируют и имеют понятную опору;
- окна, двери, трубы, props и декор не выглядят приклеенными поверх стены без встраивания;
- ground совпадает между состояниями одного уровня.

## Style Gate

- Модель читается как fantasy mid-poly, а не как low-poly blockout.
- Силуэт понятен в изометрии на `512x384` и после уменьшения до `128x96`.
- Footprint читается и не выступает за ожидаемую клетку без причины.
- Материалы выглядят как свои ресурсы: доски, камень, металл, стекло, черепица, руническая черепица, элитные доски.
- Цвет остается ярким и пригодным для стратегии; active-состояние не уходит в grimdark.
- Эолийские мотивы используются умеренно и только там, где они поддерживают сеттинг.
- LOD1/LOD2 сохраняют основной силуэт, вход, крышу и ключевые props.

## Runtime PNG Gate

- PNG имеет прозрачный фон.
- Для building sprites размер `512x384`, anchor `[256, 292]`, если spec не задает другое.
- Непрозрачные пиксели не касаются краев кадра.
- Нижняя грань alpha bounds близка к anchor по Y.
- Нет пустых прозрачных кадров.
- Состояния одного уровня не прыгают по положению и масштабу.
- Contact sheet создан с одинаковой раскладкой для preview/full.

## LOD Gate

- Для каждого `level/state` есть LOD0/LOD1/LOD2 GLB или в manifest явно указано допустимое исключение.
- Triangle counts входят в budget.
- Bounds LOD1/LOD2 близки к LOD0 и не ломают footprint.
- LOD2 не теряет главный тип здания: вход, крыша, основная масса и ключевой материал остаются узнаваемыми.

## Manifest И Frontend Gate

- `manifest.json` содержит все уровни/состояния/shape-варианты.
- PNG и GLB пути из manifest реально существуют.
- Новое семейство добавлено в `buildingAssetManifests.ts`.
- State policy в `buildingRegistry.ts` не требует отдельного кода, если хватает default policy.
- Для shape lookup и runtime-статусов поверх active добавлены тесты registry, если они нужны.
- Dev-панель `?assets=1` не показывает missing lookup для нового семейства.

## Рецепты

### Новое Здание

1. Создать spec из `docs/assets/specs/template.yaml`.
2. Заполнить material map по стоимости из `shared/catalog/buildings.ts` и docs.
3. Использовать component library для стен, крыши, дверей, окон, фундамента и props.
4. Запустить dry-run, затем preview.
5. После review запустить full.
6. Прогнать validators и добавить frontend manifest entry.
7. Обновить `asset-generation-status.md`.

### Ресурсный Prop

1. Выбрать compact spec с малым triangle budget.
2. Сохранить узнаваемый силуэт ресурса на маленьком размере.
3. Сгенерировать LOD0/LOD1/LOD2 и PNG/icon preview.
4. Проверить manifest против resource catalog, если ресурс подключается к UI.

### Руина

1. Не перекрашивать active; моделировать реальные обрушения.
2. Сохранить узнаваемую функцию исходного здания.
3. Добавить обломки на ground как отдельные props.
4. Проверить, что висящие части имеют опору или удалены.

### Vegetation Tile

1. Использовать `vegetation-artist`, `environment-artist`, `asset-optimization`.
2. Держать землю совместимой с terrain tile.
3. Делать читаемые кластеры, а не равномерный шум.
4. Проверить alpha bounds и small-scale readability.

### Пересборка Только PNG

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target png
python3 tools/assets/validate_building_sprites.py
```

### Пересборка Только LOD

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target lod
python3 tools/assets/validate_building_lods.py
```

### Пересборка Manifest Или Contact Sheet

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target manifest
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target contact-sheet
python3 tools/assets/validate_building_manifests.py
```
