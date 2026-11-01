# Стартовая сцена и знак Эолии

Изометрическая сцена стартовой страницы рендерится в Blender из оригинальных игровых GLB-моделей ратуши и жилья, геометрии игрового ландшафта, дороги, сада и леса. Эмблема Эолии также моделируется и рендерится в Blender. В интерфейсе эмблема стоит рядом с текстовым названием, набранным текущим системным шрифтом проекта.

Исходники сцен: `tools/assets/ui/start-city/start-city.blend` и `tools/assets/ui/favicon/eolia-emblem.blend`. Воспроизводимый Blender-генератор: `tools/assets/ui/build_start_blender_assets.py`. Экспорт размеров WebP и favicon: `tools/assets/ui/export_start_blender_assets.py`.

- `settlement-960.webp` — desktop-рендер 960×656.
- `settlement-480.webp` — mobile-версия 480×328, без обрезки карты.
- `eolia-mark.png` — прозрачная эмблема для стартовой страницы.

Favicon-файлы экспортируются в `frontend/public/`: ICO с вариантами 16/32/48 px, PNG 16/32/48/180/192/512 px и `apple-touch-icon.png`. Источники — собственные игровые модели и Blender-сцены; внешние изображения и шрифты не используются. WebP-сцены вместе весят менее 72 KiB.
