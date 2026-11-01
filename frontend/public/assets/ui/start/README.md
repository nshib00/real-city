# Диорама первого входа

Оригинальная векторная сцена Эолии, созданная для Real City: центр с флагом, мастерская, грядки, дорога и лес. Сторонние изображения, шрифты и приватные данные игроков не используются. Исходник и изображения распространяются на условиях MIT; © 2026 Real City contributors.

Источник: `tools/assets/ui/build_start_scene.py`; редактируемый результат — `settlement.svg`, viewBox 960×720. WebP: 480×360 и 960×720, quality 85. SVG служит лёгким fallback, в том числе при ошибке загрузки WebP. Геометрия автономная, зависимости игрового рендера не нужны.

Экспорт из корня: `python tools/assets/ui/build_start_scene.py`. Проверенные инструменты: Python 3, CairoSVG 2.9.1, Pillow 13.0.0; зависимости нужны только для экспорта.

Установка в отдельное окружение: `python -m venv /tmp/real-city-start-tools`, затем `/tmp/real-city-start-tools/bin/pip install -r tools/assets/ui/requirements-start-scene.txt`. Экспорт: `/tmp/real-city-start-tools/bin/python tools/assets/ui/build_start_scene.py`.

Бюджет: SVG ≤ 12 KiB, mobile WebP ≤ 20 KiB, desktop WebP ≤ 40 KiB, все три ≤ 72 KiB. Фактически: 7 880 / 13 246 / 28 390 байт. Размеры зарезервированы в HTML; движение отсутствует, reduced motion соблюдается автоматически.
