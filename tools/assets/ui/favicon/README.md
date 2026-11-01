# Эмблема и favicon Эолии

Собственная трёхмерная эмблема Real City: стилизованный дом на изометрическом каменном тайле, зелёная кровля и латунная лента ветра. Геометрия и материалы созданы в Blender, без внешних моделей, изображений и шрифтов.

- `eolia-emblem.blend` — исходная сцена и камера.
- `eolia-emblem-512.png` — прозрачный PNG-рендер из Blender.
- `frontend/public/favicon.ico` — 16/32/48 px.
- `frontend/public/favicon-{16,32,48,180,192,512}.png`, `apple-touch-icon.png` — браузерные варианты.
- `frontend/public/assets/ui/start/eolia-mark.png` — эмблема на экране входа; текст «Эолия» использует действующий UI-шрифт.

Пересборка: `python3 tools/assets/ui/build_start_scene.py`. Экспортёр объединяет рендер Blender с оптимизацией размеров PNG/WebP.
