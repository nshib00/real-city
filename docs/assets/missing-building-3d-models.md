# Постройки без готовых 3D-моделей

Срез на 1 ноября 2026 года. Уровни взяты из действующего `data/buildings/catalog-v2.json`, состояния — из основных визуальных спецификаций и production-манифестов. Проверено наличие непустых отдельных `.glb` для каждой пары «уровень × состояние» в `frontend/public/assets/buildings/` и `frontend/src/assets/buildings/`. Тестовые и пилотные семейства не учитываются. Это проверка наличия файлов, а не художественная приёмка, проверка всех LOD и вариантов стыковки или гарантия загрузки в игре.

## Нет моделей ни для одного уровня

Для всех строк ниже отсутствуют все перечисленные состояния на всех перечисленных уровнях. `active` — готовая постройка, `construction` — строительство, `damaged` — повреждение, `ruined` — разрушение.

| Постройка | Игровые уровни | Отсутствующие состояния |
| --- | --- | --- |
| Многоквартирный дом (`apartment_house`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Жилой небоскрёб (`residential_skyscraper`) | 5 | `active`, `construction`, `damaged`, `ruined` |
| Дворец (`palace`) | 5 | `active`, `construction`, `damaged`, `ruined` |
| Мастерская (`workshop`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Кирпичная печь (`brick_kiln`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Кузница (`forge`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Оптическая мастерская (`optical_workshop`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Монетный двор (`mint`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Рынок (`market`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Союзный дом (`alliance_house`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Сахарная грядка (`sugar_bed`) | 1–9 | `active`, `construction`, `damaged`, `ruined`, `stage01`–`stage04`, `super_stage01`–`super_stage06` |
| Железный рудник (`iron_mine`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Камнедробилка (`stone_cutters`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Химическая мастерская (`chemical_workshop`) | 1 | `active`, `construction`, `damaged`, `ruined` |
| Завод точной механики (`precision_workshop`) | 1 | `active`, `construction`, `damaged`, `ruined` |

## Модели есть частично

| Постройка | Уже есть | Отсутствующие уровни и состояния |
| --- | --- | --- |
| Вилла (`villa`) | `active` на уровнях 1–5 | `construction`, `damaged` на уровнях 1–5 |
| Грядка ветролиста (`field_bed`, ассеты `windleaf_bed`) | Все стадии роста, `active`, `construction`, `damaged` на уровнях 1–3 | `ruined` на уровнях 1–11; все остальные состояния из спецификации (`active`, `construction`, `damaged`, `stage01`–`stage04`, `super_stage01`–`super_stage06`) на уровнях 4–11 |
| Лесопильный двор (`lumber_yard`) | `active`, `construction`, `damaged` на уровнях 1–13 | `ruined` на уровнях 1–13 |
| Песчаный карьер (`sand_quarry`) | `active`, `construction`, `damaged` на уровнях 1–11 | `ruined` на уровнях 1–11 |
| Шахта (`mine`) | `active`, `construction`, `damaged` на уровнях 1–12 | `ruined` на уровнях 1–12 |

У `field_bed` frontend-реестр сейчас объявляет только уровни 1–10, хотя игровой каталог содержит 11. После создания ассета уровня 11 потребуется обновить и реестр. Отсутствующее состояние может показываться через fallback, но отдельной готовой 3D-модели для него нет.
