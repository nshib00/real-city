# Тайлы местности

Игра использует PNG как формат текстур поля.

Актуальный набор: семь типов местности и две дополнительные плотности леса.
`forest.png` соответствует плотности 3, `forest_thinned.png` плотности 2,
`forest_sparse.png` плотности 1. После очистки используется `grass.png`.

Исходник: `terrain_tiles.blend`, отдельные модели: `<terrain>.glb`.
PNG: 512x512, ширина основания 480px, anchor [256,320]. Полные параметры
находятся в `manifest.json`; runtime сохраняет пропорции и стыковку сетки.

Старый локальный генератор PNG без Blender перезаписывает актуальные рендеры
временными заглушками и не должен запускаться для production-ассетов:

```bash
python3 tools/assets/generate_terrain_tile_pngs.py
```

Blender-генератор для полноценного набора PNG:

```bash
blender --background --python tools/assets/blender/generate_terrain_tile_models.py
```

Blender-рендеры сохраняются рядом как `grass.png`, `forest.png`, `water.png`, `mountain.png`, `road.png`, `oil_well.png`, `ruins.png` и две плотности леса.
Идентификаторы совпадают с terrain API, поэтому эти PNG можно подключать без переименования.

Проверка: `python3 tools/assets/validate_terrain_models.py`.
Предпросмотр: `terrain_tiles_contact_sheet.png`; отчеты: `validation.json`
и `roundtrip-validation.json`.
