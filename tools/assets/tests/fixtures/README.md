# Fixtures пайплайна Blender-ассетов

Эта директория хранит compatibility fixtures для мигрированных legacy-генераторов.

Генераторы фазы 5 записывают JSON в `blender-assets/<asset_id>.json` после успешной сборки в Blender. Фикстура фиксирует:

- уровни и состояния ассета;
- размер и anchor PNG-спрайта;
- диапазоны треугольников;
- bounds каждой state-collection;
- ожидаемые PNG/GLB пути.

Фикстуры нужны для проверки миграции без визуального дрейфа: если генератор переписывается на component/spec API, новые bounds, anchor и triangle ranges должны оставаться совместимыми с этими файлами либо меняться осознанно.

`animation-manifests/` хранит smoke fixtures для нового runtime-контракта анимаций. Они проверяют структуру `atlas`, `animations`, anchor, directions и frame prefixes без необходимости хранить реальные тяжелые atlas-картинки.
