# UI-графика Blender

Сцена стартового экрана и эмблема Эолии являются оригинальными Blender-ассетами проекта. Для стартовой диорамы используется runtime-геометрия игровых моделей ратуши и жилья, дополненная сеткой карты, дорогой, садом и лесом. Для эмблемы используется отдельная оптимизированная сцена.

- `build_start_blender_assets.py` — собирает и рендерит `.blend`-сцены с CPU через Cycles.
- `export_start_blender_assets.py` — готовит WebP, PNG, ICO и Apple touch icon для публичного каталога.
- `build_start_scene.py` — совместимая команда, запускающая обе стадии через установленный `blender` и `python3`.
- `build_icon_set.py`, `export_pilot.py`, `check_pilot.py` — отдельные инструменты интерфейсных иконок и пилота.
- `favicon/` — исходная сцена эмблемы и описание её браузерных экспортов.
- `start-city/` — исходная сцена карты и Blender-рендер для проверки качества.

Пересборка из корня: `python3 tools/assets/ui/build_start_scene.py`. Нужны Blender с Cycles и Pillow для экспорта PNG/WebP.
