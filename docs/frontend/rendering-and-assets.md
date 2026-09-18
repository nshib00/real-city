# Рендеринг и ассеты

## Общая схема карты

Карта состоит из двух слоев:

1. Pixi.js canvas для тайлов мира.
2. React/DOM-слой поверх canvas для зданий, ресурсных узлов, монстров, таймеров и кнопок выбора объектов.

Главный компонент карты: `frontend/src/game/IsoMap.tsx`.

`IsoMap`:

- получает состояние камеры, viewport, выбранных объектов и объектов мира из `useGameStore`;
- загружает видимые чанки через `useVisibleChunks`;
- передает тайлы в `PixiStage`;
- обрабатывает drag-pan, wheel-zoom, выбор тайла;
- показывает здания, ресурсные узлы и монстров поверх карты;
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
| `wrapCameraOffset` | Оборачивание смещения камеры |
| `nearestWrappedScreenCoord` | Поиск ближайшей экранной позиции с учетом wrap мира |

## Pixi-слой тайлов

Файл: `frontend/src/game/renderer/PixiStage.tsx`.

`PixiStage` создает `Application` Pixi, добавляет контейнеры для:

- PNG-спрайтов тайлов;
- fallback-графики тайлов;
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
- `onPointerMove` обновляет hover-тайл, если пользователь не тащит карту;
- `onPointerLeave` сбрасывает hover.

## Текстуры terrain

Файл: `frontend/src/game/renderer/terrainTextures.ts`.

Публичные PNG лежат в `frontend/public/assets/terrain/tiles/` и доступны по URL `/assets/terrain/tiles/<name>.png`.

Для леса выбирается вариант по `forest_density`:

- обычный `forest.png`;
- `forest_thinned.png` при плотности `2`;
- `forest_sparse.png` при плотности `1`.

`preloadTerrainPngTextures()` прогружает все основные terrain-спрайты через Pixi `Assets.load`.

## DOM-объекты карты

DOM-слой находится в `IsoMap.tsx` внутри `.map-origin`.

Для каждого видимого здания рендерится `MapObject` с классами:

- `map-building`;
- `map-building-<kind>`;
- `map-building-construction`, если здание строится;
- `map-building-selected`, если выбрано.

Для зданий подключены модели:

- `TownHallModel`;
- `DugoutModel`;
- `WoodHouseModel`;
- `LumberYardModel`.

Если здание строится, поверх объекта показывается `construction-timer`.

Ресурсные узлы получают CSS-класс и подпись из `frontend/src/game/renderers/resources.ts`.

Монстры получают CSS-класс и подпись из `frontend/src/game/renderers/monsters.ts`, а здоровье показывается полосой `monster-health`.

## Рендер зданий

Есть две параллельные схемы ассетов зданий:

1. PNG-спрайты через `BuildingSpriteImage`.
2. GLB-модели через `BuildingGlbModel`.

### PNG-спрайты

Файлы:

- `frontend/src/game/renderers/BuildingSpriteImage.tsx`;
- `frontend/src/game/renderers/buildingSpriteAssets.ts`.

`buildingSpriteAsset(building)` возвращает публичный URL вида:

```text
/assets/buildings/<category>/<building>/<building>_l<level>_<state>.png
```

Сейчас PNG-подбор явно поддерживает:

- `town_hall`;
- `dugout`;
- `wood_house`;
- `lumber_yard`.

### GLB-модели

Файлы:

- `frontend/src/game/renderers/BuildingGlbModel.tsx`;
- `frontend/src/game/renderers/buildingModelAssets.ts`.

`BuildingGlbModel` создает Three.js renderer на canvas, грузит GLB через `GLTFLoader`, ставит ортографическую камеру и освещение, затем подгоняет модель под ячейку функцией `fitModelToCell`.

Для `town_hall`, `dugout`, `wood_house` GLB импортируются из `frontend/src/assets/buildings/...` через `?url`, чтобы сборщик Vite обработал их как ассеты.

Для `lumber_yard` GLB берется публичным URL:

```text
/assets/buildings/industry/lumber_yard/lumber_yard_l<level>_<state>.glb
```

Это важное отличие при добавлении новых зданий: нужно заранее выбрать, ассет импортируется сборщиком из `src/assets` или лежит публично в `public/assets`.

## Уровни и состояния моделей

Для каждой поддержанной визуальной ветки есть отдельный файл с правилами уровня и состояния:

| Постройка | Файл |
| --- | --- |
| Ратуша | `frontend/src/game/renderers/townHall.ts` |
| Землянка | `frontend/src/game/renderers/dugout.ts` |
| Деревянный дом | `frontend/src/game/renderers/woodHouse.ts` |
| Лесопильный двор | `frontend/src/game/renderers/lumberYard.ts` |

Эти файлы решают, какой уровень ассета и какое состояние (`active`, `construction`, `damaged`, `ruined`) показывать для `PlacedBuilding`.

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
3. Добавить ассеты в выбранную схему: `public/assets` или `src/assets`.
4. Добавить правила уровня/состояния в `frontend/src/game/renderers/<building>.ts`.
5. Подключить новый тип в `buildingSpriteAssets.ts` или `buildingModelAssets.ts`.
6. Создать компонент модели по аналогии с `TownHallModel`, `DugoutModel`, `WoodHouseModel`, `LumberYardModel`.
7. Подключить компонент в `IsoMap.tsx` при рендере `visibleBuildings`.
8. Добавить тесты для правил выбора ассета.

## Текущие ограничения

- В `IsoMap.tsx` визуальные компоненты подключены явно по `building.kind`; для многих типов из каталога пока нет индивидуального рендера.
- PNG и GLB схемы ассетов смешаны, поэтому при добавлении здания нужно проверить оба слоя.
- `NotificationCenter` и часть `EventLog` пока используют статические данные и не отражают realtime-события напрямую.
