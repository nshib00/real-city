# Рендеринг и ассеты

## Общая схема карты

Карта состоит из трех логических слоев:

1. Pixi.js canvas для тайлов мира.
2. Pixi object layer для построек, ресурсных узлов и монстров.
3. React/DOM-слой поверх canvas только для UI-оверлеев: таймеров, бейджей производства, HUD и панелей.

Главный компонент карты: `frontend/src/game/IsoMap.tsx`.

`IsoMap`:

- получает состояние камеры, viewport, выбранных объектов и объектов мира из `useGameStore`;
- загружает видимые чанки через `useVisibleChunks`;
- передает тайлы, постройки, ресурсные узлы и монстров в `PixiStage`;
- обрабатывает drag-pan, wheel-zoom, выбор тайла;
- показывает интерактивные UI-оверлеи построек поверх карты;
- запускает рубку леса при клике на подходящий лесной тайл;
- фильтрует видимые объекты через `filterVisibleMapObjects`.

## Изометрические координаты

Файл: `frontend/src/game/coordinates/iso.ts`.

Основные константы:

- `TILE_WIDTH = 240`;
- `TILE_HEIGHT = 120`;
- `CHUNK_SIZE = 32`;
- `WORLD_WRAP_TILES = 160`.

Основные функции:

| Функция | Назначение |
| --- | --- |
| `gridToScreen` | Перевод координат тайла в экранную изометрию |
| `screenToGrid` | Обратный перевод экрана в координаты тайла |
| `tileToChunk` | Определение чанка по тайлу |
| `roundGridCoord` | Округление координат до тайла |
| `wrapGridCoord` | Оборачивание координат мира |
| `nearestWrappedScreenCoord` | Поиск ближайшей экранной позиции с учетом wrap мира и непрерывного смещения камеры |

## Pixi-Слой Карты

Файл: `frontend/src/game/renderer/PixiStage.tsx`.

`PixiStage` создает `Application` Pixi, добавляет контейнеры для:

- PNG-спрайтов тайлов;
- fallback-графики тайлов;
- построек;
- ресурсных узлов;
- монстров;
- анимационных оверлеев построек;
- overlay выбранного/hover-тайла.

Тайлы сортируются по `y`, затем `x`, чтобы изометрический порядок выглядел корректнее. Если для типа terrain есть PNG-текстура, рисуется спрайт. Если текстуры нет, рисуется цветной ромб через `Graphics`.

Поддержанные fallback-цвета:

- `grass`;
- `forest`;
- `water`;
- `mountain`;
- `road`;
- `oil_well`;
- `ruins`.

События мыши:

- `onClick` переводит позицию указателя в tile через `eventToTile`;
- перед выбором тайла проверяет hit areas построек, ресурсных узлов и монстров;
- `onPointerMove` обновляет hover-тайл, если пользователь не тащит карту;
- `onPointerLeave` сбрасывает hover.

Постройки, ресурсы и монстры больше не имеют массового DOM fallback. Если для постройки нет зарегистрированного PNG в manifest registry, Pixi рисует процедурный fallback, чтобы объект не исчезал с карты.

## Текстуры terrain

Файл: `frontend/src/game/renderer/terrainTextures.ts`.

Публичные PNG лежат в `frontend/public/assets/terrain/tiles/` и доступны по URL `/assets/terrain/tiles/<name>.png`.

Для леса выбирается вариант по `forest_density`:

- обычный `forest.png`;
- `forest_thinned.png` при плотности `2`;
- `forest_sparse.png` при плотности `1`.

`preloadTerrainPngTextures()` прогружает все основные terrain-спрайты через Pixi `Assets.load`.

## DOM-Оверлеи Карты

DOM-слой находится в `IsoMap.tsx` внутри `.map-origin`, но не рисует массовые игровые объекты. Он оставлен для UI-элементов, которым полезна обычная React-интерактивность:

- `construction-timer`;
- `BuildingWorkBadge`;
- кликабельные бейджи производства и сбора;
- dev `Performance HUD`.

Сами постройки, ресурсы и монстры выбираются через Pixi hit areas. Это убирает дублирование DOM/Pixi путей и не требует отдельного подключения React-компонента для каждого нового типа объекта.

## Рендер зданий

Основной runtime-путь построек на карте:

1. `buildingAssetManifests.ts` описывает доступные PNG/atlas/GLB источники.
2. `buildingRegistry.ts` выбирает состояние и URL ассета.
3. `objectLayer/objectDrawData.ts` превращает постройки в команды Pixi.
4. `PixiStage.tsx` рисует PNG-спрайт или процедурный fallback.

Выбор конкретного файла теперь идет через manifest-driven registry:

- `frontend/src/game/renderers/buildingAssetManifests.ts` хранит компактные данные из manifests: `building.kind`, `assetId`, категорию, уровни, состояния, источник PNG/GLB и ревизию cache-busting;
- `frontend/src/game/renderers/buildingRegistry.ts` применяет правила уровня/состояния, clamped levels, damaged threshold и fallback `ruined -> damaged`, если в manifest нет отдельного ruined-ассета;
- `buildingSpriteAssets.ts`, `buildingModelAssets.ts`, roads/walls lookup и build-menu preview используют registry, а не отдельные ручные таблицы путей.

### PNG-Спрайты

Файлы:

- `frontend/src/game/renderers/BuildingSpriteImage.tsx`;
- `frontend/src/game/renderers/buildingSpriteAssets.ts`.

`buildingSpriteAsset(building)` возвращает публичный URL вида:

```text
/assets/buildings/<category>/<building>/<building>_l<level>_<state>.png
```

PNG-подбор поддерживает все семьи, зарегистрированные в `buildingAssetManifests.ts`, включая modular roads/walls через shape-aware URL.

`BuildingSpriteImage` сохраняется для preview/debug UI, но карта не использует его как массовый слой.

### GLB-модели

Файлы:

- `frontend/src/game/renderers/BuildingGlbModel.tsx`;
- `frontend/src/game/renderers/buildingModelAssets.ts`.

`BuildingGlbModel` создает Three.js renderer на canvas, грузит GLB через `GLTFLoader`, ставит ортографическую камеру и освещение, затем подгоняет модель под ячейку функцией `fitModelToCell`. Начальный ракурс изометрический с учетом оси Y как вертикали GLB; модель можно вращать перетаскиванием мышью или касанием и приближать колесом мыши или жестом масштабирования.

GLB не используется как runtime-рендер карты. Он доступен только в preview/debug интерфейсах через `BuildingModelPreview`, чтобы карта не создавала сотни Three/WebGL contexts.

Для `town_hall`, `dugout`, `wood_house` GLB остаются в `frontend/src/assets/buildings/...` и подключаются через `import.meta.glob(..., { query: '?url' })`, чтобы сборщик Vite обработал их как ассеты.

Для новых партий GLB берется публичным URL:

```text
/assets/buildings/<category>/<building>/<building>_l<level>_<state>.glb
```

Стандарт для новых моделей: `frontend/public/assets/buildings/<category>/<asset_id>/`. `src/assets` сохраняется только для legacy GLB, которые уже импортируются сборщиком.

## Уровни и состояния моделей

Для legacy и специализированных веток остаются отдельные файлы с правилами уровня и состояния:

| Постройка | Файл |
| --- | --- |
| Ратуша | `frontend/src/game/renderers/townHall.ts` |
| Землянка | `frontend/src/game/renderers/dugout.ts` |
| Деревянный дом | `frontend/src/game/renderers/woodHouse.ts` |
| Лесопильный двор | `frontend/src/game/renderers/lumberYard.ts` |

`buildingRegistry.ts` вызывает эти правила через registry policy и затем сверяет результат с states из manifest.
После завершения строительства или апгрейда здание без критического урона всегда должно использовать `active`-ассет. `damaged`-ассет применяется только при `health <= 20% max_health`; один лишь backend-state `damaged` не должен переключать модель, если HP выше этого порога.

## Debug экран ассетов

В dev-сборке можно открыть runtime-проверку registry через query flag:

```text
http://localhost:5173/?assets=1
```

Панель `frontend/src/features/assets/AssetDebugPanel.tsx` показывает зарегистрированные семьи, уровни, состояния, PNG preview, GLB ссылку и локальные ошибки lookup. В обычном режиме игры панель не рендерится.

## Ассеты ресурсов

Файл компонента: `frontend/src/features/resources/ResourceIcon.tsx`.

PNG-иконки ресурсов лежат в `frontend/public/assets/resources/icons/` и доступны по URL:

```text
/assets/resources/icons/<resource-id>.png
```

Если PNG не загрузился, `ResourceIcon` показывает fallback-иконку `Package` из lucide-react.

Реестр всех ресурсов находится в `frontend/src/features/resources/ResourceRegistry.tsx`.

## Где лежат ассеты

| Каталог | Содержимое |
| --- | --- |
| `frontend/public/assets/terrain/tiles` | PNG/SVG тайлов, manifest и отчеты валидации |
| `frontend/public/assets/buildings` | PNG-состояния зданий, часть публичных GLB/отчетов |
| `frontend/public/assets/resources/icons` | PNG-иконки ресурсов и manifest |
| `frontend/src/assets/buildings` | Импортируемые GLB и README по наборам моделей |
| `frontend/src/assets/resources` | README по ресурсным ассетам |

## Как добавить визуал новой постройки

1. Добавить тип постройки в общий каталог `shared/catalog/buildings.ts` и в `BuildingKind` в `frontend/src/game/state/useGameStore.ts`, если типа еще нет.
2. Добавить описание в `frontend/src/features/buildings/catalog.ts`, если постройка должна быть в меню строительства.
3. Положить новые ассеты в `frontend/public/assets/buildings/<category>/<asset_id>/` вместе с `manifest.json`.
4. Добавить compact manifest entry в `buildingAssetManifests.ts`: `kind`, `assetId`, `category`, `levels`, `states`, source и revision при необходимости.
5. Если нужны особые правила уровня/состояния, добавить policy в `buildingRegistry.ts`; иначе будет использован общий active/construction/damaged/ruined policy.
6. Добавить тесты registry lookup: clamped levels, construction, damaged threshold, fallback для отсутствующих states.
7. Если PNG еще не готов, убедиться, что procedural fallback в Pixi приемлем как временный placeholder.

## Текущие ограничения

- PNG и GLB схемы ассетов смешаны только для legacy `src/assets`; новые модели должны идти через `public/assets`.
- `NotificationCenter` и часть `EventLog` пока используют статические данные и не отражают realtime-события напрямую.

## Семантика интерфейса Эолии

Владение, выбор и состояние рисуются независимыми слоями. Цвет не должен быть единственным различием: круг с точкой для своего, связанный знак союза, ромб чужого, пустой контур нейтрального; угроза отмечается отдельным знаком и текстом. Материалы, сочетания и границы реализации описаны в [арт-дирекции UI](../art/aeolian-ui-style-guide.md). Это спецификация фазы 1; перенос в игровой renderer относится к последующим фазам.
