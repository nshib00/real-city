# Архитектура Анимированных Объектов Карты

## Назначение

Документ описывает целевую архитектуру отображения построек, монстров, ресурсных узлов и декоративных объектов на изометрической карте Real City с учетом будущих анимаций и высокой плотности мира.

Главная цель: дать игре живую анимированную карту, но не превратить каждый объект в дорогой 3D-renderer или отдельный React/DOM-узел. Карта должна оставаться плавной при тысячах объектов в мире и сотнях видимых объектов в активной области.

## Основное Решение

Целевая схема является гибридной:

1. Blender остается источником мастер-моделей, ригов, анимаций, LOD и рендеров.
2. Массовый runtime карты использует 2D-спрайты и спрайтовые атласы, отрисованные через Pixi.js.
3. GLB используется ограниченно: для инспектора, меню строительства, выбранного объекта, отладочных preview и будущих специальных крупных сцен.
4. Постройки по умолчанию являются статичными state-driven объектами с дешевыми overlay-анимациями.
5. Монстры являются полноценными animated sprites, с анимациями движения, атаки, получения урона и смерти.
6. React управляет интерфейсом, состоянием выбора и панелями, но не должен рендерить тысячи объектов карты как DOM-элементы.

## Почему Не Нужно Массово Рендерить GLB На Карте

Текущий компонент `frontend/src/game/renderers/BuildingGlbModel.tsx` создает отдельный `Three.WebGLRenderer`, сцену, камеру и canvas для одного здания. Это приемлемо для нескольких объектов, но не подходит как базовый способ отображения карты.

Проблемы массового GLB-подхода:

- браузер ограничивает количество WebGL-контекстов;
- каждый renderer имеет собственные ресурсы, resize lifecycle и память;
- загрузка множества GLB тяжелее, чем загрузка атласов;
- скелетные анимации и mixer на сотнях объектов быстро становятся дорогими;
- React-дерево с тысячами canvas/DOM-узлов будет плохо масштабироваться;
- depth sorting изометрической карты сложнее синхронизировать между множеством независимых renderers.

Поэтому GLB должен быть мастер-форматом и форматом близкого preview, а не массовым форматом карты.

## Runtime-Слои Карты

Целевая карта должна состоять из нескольких слоев с разной ответственностью.

| Слой | Технология | Назначение |
| --- | --- | --- |
| Terrain layer | Pixi.js | Тайлы земли, воды, леса, гор, дорог, базовые overlay тайлов |
| Object base layer | Pixi.js | Статичные спрайты построек, ресурсов, декора, руин |
| Object animation layer | Pixi.js | Animated sprites и overlay-анимации: дым, огонь, флаги, работающие механизмы |
| Unit layer | Pixi.js | Монстры, будущие юниты, projectiles, временные боевые эффекты |
| Selection/debug layer | Pixi.js или DOM | Выделение, hover, радиусы, пути, зоны угрозы |
| UI layer | React/DOM | Панели, инспектор, меню строительства, журнал, уведомления |
| Preview 3D layer | Three.js | GLB-preview выбранного объекта, карточки ассетов, debug-панели |

React может передавать в Pixi-слои снимок видимого состояния и callbacks выбора, но frame-by-frame анимации должны жить внутри Pixi ticker, а не в React state.

## Категории Объектов

## Постройки

Постройки обычно не требуют полноценной скелетной анимации на карте. Основная часть визуала должна быть статичным base sprite, выбранным по типу, уровню, состоянию, форме и здоровью.

Базовые состояния:

| Состояние | Отображение |
| --- | --- |
| `construction` | Статичный sprite стройки, при необходимости overlay с пылью/искрой |
| `active` | Основной sprite здания |
| `working` | `active` sprite + один или несколько overlay-циклов |
| `idle_no_workers` | `active` sprite + приглушенный overlay или отсутствие working-анимации |
| `damaged` | Поврежденный sprite, дым/искры как overlay |
| `ruined` | Руины, обычно без постоянной анимации |
| `upgrading` | Текущий sprite + scaffolding/worker overlay |
| `under_attack` | Боевой overlay: вспышки, огонь, damage numbers |
| `ready_to_collect` | UI overlay, не отдельное состояние модели |

Постоянная анимация здания должна быть исключением. Например, мельница, кузница, насос, фабрика или энергетический объект могут иметь небольшой loop, но он должен быть реализован как overlay-спрайт, а не как отдельный GLB-renderer.

## Монстры

Монстры должны использовать полноценные sprite-анимации, потому что движение и бой являются частью читаемости игры.

Базовый набор анимаций:

| Анимация | Назначение |
| --- | --- |
| `idle` | Стоит, дышит, оглядывается |
| `walk` | Движение между тайлами |
| `attack` | Удар или дальняя атака |
| `hit` | Получение урона |
| `death` | Смерть и исчезновение |
| `spawn` | Появление, если нужно для особых спавнов |
| `roar` | Сигнал угрозы или агро-состояния |

Для старта достаточно четырех направлений: `ne`, `nw`, `se`, `sw`. Когда появится потребность в более плавном движении, можно расширить до восьми направлений.

## Ресурсные Узлы

Ресурсные узлы должны быть дешевле построек:

- base sprite по типу ресурса и состоянию истощения;
- короткие overlay-анимации только для важных узлов или близкого зума;
- возможные состояния: `full`, `claimed`, `depleted`, `contested`, `guarded`;
- GLB-preview допустим в инспекторе, но не на массовой карте.

## Дороги И Стены

Дороги и стены являются shape-based объектами. Для них важнее правильный подбор формы, чем анимация.

Требования:

- shape-aware lookup: `single`, `straight`, `corner`, `t`, `cross`, `end`;
- состояние `active`, `construction`, `damaged`, `ruined`;
- atlas sprites вместо отдельных DOM-изображений;
- анимации только поверх: пыль от движения, подсветка логистики, огонь при осаде.

## Форматы Ассетов

## Статичные Спрайты

Статичные sprite-файлы остаются основой для построек.

Рекомендуемый формат:

```text
frontend/public/assets/buildings/<category>/<asset_id>/<asset_id>_l03_active.png
frontend/public/assets/buildings/<category>/<asset_id>/<asset_id>_l03_damaged.png
frontend/public/assets/buildings/<category>/<asset_id>/<asset_id>_l03_ruined.png
```

Текущий стандарт PNG для построек:

- размер: `512x384`;
- прозрачный фон;
- anchor: `[256, 292]`;
- единая камера и свет внутри семейства;
- читаемость после уменьшения примерно до `128x96`.

Позже PNG можно заменить или дополнить WebP/AVIF, но manifest должен скрывать конкретный формат от игрового кода.

## Спрайтовые Атласы

Для массового runtime отдельные PNG-файлы нужно собирать в атласы.

Преимущества атласов:

- меньше HTTP-запросов;
- лучше batching в Pixi;
- меньше переключений текстур на GPU;
- удобнее хранить frame-анимации;
- проще кешировать версионированные ассеты.

Рекомендуемый набор:

```text
frontend/public/assets/buildings/<category>/<asset_id>/<asset_id>.atlas.json
frontend/public/assets/buildings/<category>/<asset_id>/<asset_id>.webp
frontend/public/assets/monsters/<monster_id>/<monster_id>.atlas.json
frontend/public/assets/monsters/<monster_id>/<monster_id>.webp
```

На переходном этапе можно продолжать использовать отдельные PNG и добавить атласы постепенно.

## GLB

GLB продолжает экспортироваться из Blender:

```text
<asset_id>_l03_active_LOD0.glb
<asset_id>_l03_active_LOD1.glb
<asset_id>_l03_active_LOD2.glb
```

Использование GLB:

- 3D-preview в инспекторе;
- debug-панель ассетов;
- меню строительства для дорогих/важных построек;
- генерация PNG/атласов из единого мастер-источника;
- возможный future mode для очень близкого cinematic zoom, если он появится.

GLB не должен быть обязательным для отображения каждого здания на карте.

## Manifest Контракт

Manifest должен стать единым контрактом между Blender-пайплайном и frontend registry.

Минимальный manifest для здания:

```json
{
  "assetId": "sawmill_yard",
  "kind": "sawmill_yard",
  "category": "industry",
  "footprint": [1, 1],
  "anchor": [256, 292],
  "levels": [1, 2, 3],
  "states": ["construction", "active", "damaged", "ruined"],
  "render": {
    "mode": "sprite",
    "size": [512, 384],
    "preferredFormat": "webp",
    "fallbackFormat": "png"
  },
  "atlas": {
    "image": "sawmill_yard.webp",
    "json": "sawmill_yard.atlas.json",
    "revision": "2026-10-12"
  },
  "animations": {
    "working": {
      "type": "overlay",
      "fps": 8,
      "frames": 12,
      "loop": true,
      "anchor": [256, 292],
      "framePrefix": "sawmill_yard_l03_working_"
    },
    "smoke": {
      "type": "shared_overlay",
      "id": "smoke_small",
      "fps": 6,
      "loop": true
    }
  },
  "glb": {
    "lod0": "sawmill_yard_l03_active_LOD0.glb",
    "lod1": "sawmill_yard_l03_active_LOD1.glb",
    "lod2": "sawmill_yard_l03_active_LOD2.glb"
  }
}
```

Минимальный manifest для монстра:

```json
{
  "monsterId": "ruins_guardian",
  "anchor": [128, 190],
  "directions": ["ne", "nw", "se", "sw"],
  "atlas": {
    "image": "ruins_guardian.webp",
    "json": "ruins_guardian.atlas.json",
    "revision": "2026-10-12"
  },
  "animations": {
    "idle": { "fps": 6, "frames": 8, "loop": true },
    "walk": { "fps": 10, "frames": 12, "loop": true },
    "attack": { "fps": 12, "frames": 10, "loop": false },
    "hit": { "fps": 10, "frames": 5, "loop": false },
    "death": { "fps": 10, "frames": 14, "loop": false }
  },
  "glb": {
    "preview": "ruins_guardian_preview.glb"
  }
}
```

## Blender-Пайплайн Для Построек

Постройки создаются и поддерживаются в Blender как мастер-сцены. Из них экспортируются GLB LOD и рендерятся sprites/overlays.

Этапы:

1. Создать или обновить spec в `docs/assets/specs/**/*.yaml`.
2. Собрать мастер-сцену через общий API `tools/assets/blender/real_city/`.
3. Разделить объект на base geometry и optional animated parts.
4. Настроить единую ортографическую изометрическую камеру.
5. Экспортировать LOD0/LOD1/LOD2 GLB.
6. Отрендерить base sprites для `level/state`.
7. Отрендерить overlay-анимации, если они есть.
8. Собрать atlas и manifest.
9. Создать contact sheet.
10. Запустить валидаторы bounds, alpha, manifest, LOD и roundtrip.

Правило для зданий: если анимируется только маленькая деталь, она должна быть overlay, а не полной перерисовкой всего здания на каждый кадр.

Примеры overlay-анимаций:

- дым из трубы;
- искры кузницы;
- вращение колеса;
- мерцание окон;
- флаги и ткань;
- пыль стройки;
- огонь при повреждении;
- световой импульс готового производства.

## Blender-Пайплайн Для Монстров

Монстры создаются как ригованные модели.

Этапы:

1. Создать monster spec с габаритами, silhouette notes, поведением и набором actions.
2. Смоделировать или сгенерировать модель в стиле проекта.
3. Сделать retopology/упрощение под preview GLB.
4. Создать rig.
5. Создать actions: `idle`, `walk`, `attack`, `hit`, `death`.
6. Настроить render directions: минимум `ne`, `nw`, `se`, `sw`.
7. Отрендерить sprite frames для каждой пары `animation + direction`.
8. Собрать atlas.
9. Экспортировать preview GLB с actions для инспектора и отладки.
10. Проверить читаемость на размере игрового спрайта.

Важно: направление монстра в игре должно вычисляться из его движения или цели атаки, а не задаваться вручную в визуальном слое.

## Выбор Визуального Состояния

Frontend registry должен выбирать визуал из доменного состояния объекта.

Для здания:

1. Определить `kind`.
2. Clamp уровня к доступным уровням manifest.
3. Определить base state:
   - строится или улучшается: `construction`;
   - разрушено: `ruined`;
   - критический урон: `damaged`;
   - иначе: `active`.
4. Определить activity overlays:
   - производство работает: `working`;
   - производство готово: `ready_to_collect`;
   - атакуется: `under_attack`;
   - горит или недавно получил урон: `fire/smoke`.
5. Подобрать atlas frame или fallback PNG.

Для монстра:

1. Определить `type`.
2. Определить action из server state: `idle`, `moving`, `attacking`, `hit`, `dead`.
3. Преобразовать action в animation key.
4. Определить направление по velocity или target direction.
5. Подобрать animation frames.
6. Запустить или сменить animation clip без React rerender на каждый кадр.

## Depth Sorting

Изометрический порядок должен быть централизованным.

Базовая формула сортировки:

```text
sortKey = tileY + tileX + layerOffset + footprintOffset
```

Рекомендуемые правила:

- terrain ниже всех объектов;
- дороги ниже зданий и юнитов;
- здания сортируются по основанию, а не по верхней точке sprite;
- footprint больших зданий учитывается через нижний/передний тайл;
- монстры и юниты сортируются по текущей interpolated position;
- selection rings рисуются под объектом;
- health bars и badges рисуются над объектом в отдельном overlay layer.

Функция `frontend/src/game/renderer/depth.ts` должна остаться единой точкой правил сортировки, а Pixi object layer должен использовать те же принципы.

## Производительность

## Бюджеты

Ориентиры для одной активной области карты:

| Категория | Целевой бюджет |
| --- | --- |
| Видимые тайлы | Зависит от viewport и чанков, только текущий радиус |
| Видимые постройки | Сотни объектов через batched sprites |
| Видимые монстры | Десятки или низкие сотни animated sprites |
| Постоянные overlay-анимации | Только близкий зум или важные объекты |
| GLB на карте | 0 по умолчанию, 1-3 для preview/selected/debug |
| React DOM-объекты карты | Только UI/selection/inspector, не массовый слой |

## Правила Оптимизации

1. Не создавать отдельный canvas/renderer на каждый объект карты.
2. Не обновлять React state каждый animation frame.
3. Не хранить тысячи отдельных `img` DOM-узлов для зданий.
4. Использовать атласы и общие Texture references.
5. Рендерить только видимые объекты.
6. Отключать overlay-анимации на дальнем зуме.
7. Использовать низкий FPS для idle-анимаций.
8. Синхронизировать циклические анимации через глобальные clocks.
9. Давать объектам phase offset от стабильного `objectId`, чтобы одинаковые loops не двигались синхронно.
10. Переиспользовать shared overlays: дым, огонь, искры, готовность производства.
11. Кешировать parsed manifests и atlas textures.
12. Выгружать atlas groups, которые долго не используются.
13. Батчить health bars и selection rings, если их станет много.
14. Считать game simulation на сервере; frontend отвечает только за визуальную интерполяцию.

## Animation Clock

Pixi object layer должен иметь единый animation ticker.

Принцип:

```text
frame = floor((globalTime * fps + phaseOffset) % frameCount)
```

`phaseOffset` вычисляется стабильно:

```text
phaseOffset = hash(objectId) % frameCount
```

Это позволяет:

- не хранить локальный таймер на каждый объект;
- не обновлять React state;
- избежать синхронного движения одинаковых зданий;
- быстро приостанавливать классы анимаций по zoom или visibility.

## LOD Поведение В Runtime

LOD должен зависеть от zoom, важности объекта и выбора игрока.

| Условие | Визуал |
| --- | --- |
| Дальний zoom | Упрощенный sprite, без overlay-анимаций |
| Средний zoom | Base sprite, ограниченные важные overlays |
| Ближний zoom | Base sprite высокого качества, overlays, animated monsters |
| Выбранный объект | Полный sprite набор, UI overlays, возможно GLB-preview в инспекторе |
| Debug/asset mode | Можно показывать GLB, bounds, anchor, atlas frame |

LOD не должен менять игровую логику. Это только визуальное решение.

## Интеграция С Текущей Архитектурой

Текущая документация описывает карту как Pixi layer для тайлов и React/DOM layer для зданий, ресурсов и монстров. Целевая архитектура должна постепенно перенести массовые объекты из DOM в Pixi.

Текущие важные точки:

- `frontend/src/game/IsoMap.tsx` управляет камерой, выбором, visible filtering и объектами карты;
- `frontend/src/game/renderer/PixiStage.tsx` рисует terrain;
- `frontend/src/game/renderers/buildingRegistry.ts` выбирает ассеты зданий;
- `frontend/src/game/renderers/buildingAssetManifests.ts` хранит compact manifest metadata;
- `frontend/src/game/renderers/BuildingSpriteImage.tsx` показывает PNG в DOM;
- `frontend/src/game/renderers/BuildingGlbModel.tsx` показывает GLB через отдельный Three renderer;
- `frontend/src/game/renderers/monsters.ts` пока хранит классы и подписи монстров.

Целевое изменение:

- `IsoMap.tsx` продолжает отвечать за input, camera, selection и visible objects;
- `PixiStage.tsx` или новый sibling component получает не только tiles, но и visible object draw data;
- массовые здания, ресурсы и монстры рисуются внутри Pixi containers;
- DOM-слой оставляет только интерактивные панели и ограниченные overlays, если они нужны;
- GLB-компоненты остаются в preview/debug ветке.

## Предлагаемые Новые Модули

| Модуль | Назначение |
| --- | --- |
| `frontend/src/game/renderer/objectLayer/PixiObjectLayer.ts` | Создание Pixi containers для построек, ресурсов, монстров, overlay |
| `frontend/src/game/renderer/objectLayer/objectDrawData.ts` | Преобразование domain entities в draw commands |
| `frontend/src/game/renderer/objectLayer/objectTextureCache.ts` | Загрузка atlas/texture assets и кеширование |
| `frontend/src/game/renderer/objectLayer/objectDepth.ts` | Pixi sort keys на основе существующих depth rules |
| `frontend/src/game/renderer/objectLayer/animationClock.ts` | Единый clock и frame selection |
| `frontend/src/game/renderers/assetManifestTypes.ts` | Типы manifest для static sprites, atlas, animations, GLB |
| `frontend/src/game/renderers/monsterAssetRegistry.ts` | Registry монстров по manifest |
| `frontend/src/game/renderers/buildingAnimationRegistry.ts` | Правила overlay-анимаций построек |
| `tools/assets/build_atlas.py` | Сборка PNG/WebP atlas из rendered frames |
| `tools/assets/validate_animation_manifests.py` | Проверка manifest анимаций, frames, anchors и atlas references |

Имена можно уточнить при реализации, но разделение ответственности должно сохраниться.

## План Реализации

## Фаза 1. Зафиксировать Контракты

Цель: подготовить типы и документацию, не меняя способ отображения карты.

Задачи:

1. Добавить TypeScript-типы для расширенного asset manifest: `anchor`, `atlas`, `animations`, `glb`, `lod`.
2. Расширить существующую схему compact manifests так, чтобы она могла описывать будущие animation metadata.
3. Добавить отдельный registry для monster assets.
4. Описать mapping доменных состояний в визуальные состояния.
5. Добавить тесты на выбор base state и animation overlays.

Результат:

- текущая карта работает как раньше;
- код уже понимает новые поля manifest;
- можно добавлять анимированные ассеты без изменения доменной модели.

## Фаза 2. Подготовить Blender Export Contract

Цель: научить ассетный пайплайн производить данные, нужные frontend.

Задачи:

1. Расширить `docs/assets/specs/schema.json` полями animation/atlas.
2. Добавить conventions для building overlays.
3. Добавить conventions для monster actions и directions.
4. Добавить сборку contact sheets для animation frames.
5. Добавить валидатор animation manifests.
6. Добавить smoke fixture с одной постройкой и одним монстром.

Результат:

- Blender-пайплайн может выдавать не только static PNG/GLB, но и анимационные кадры;
- валидаторы ловят ошибки anchors, frames, fps, missing atlas references.

## Фаза 3. Ввести Atlas Loader

Цель: дать frontend возможность грузить атласы параллельно со старыми PNG.

Задачи:

1. Реализовать загрузчик atlas JSON + image через Pixi Assets.
2. Добавить cache по `assetId + revision`.
3. Сделать fallback на существующий PNG URL, если atlas отсутствует.
4. Добавить unit-тесты lookup и fallback.
5. Добавить debug output в asset panel: atlas найден, frames count, missing frames.

Результат:

- существующие ассеты продолжают работать;
- новые atlas-based ассеты могут подключаться без отдельной ручной логики.

## Фаза 4. Перенести Постройки В Pixi Object Layer

Цель: убрать массовый DOM-render построек.

Задачи:

1. Создать Pixi container для building base sprites.
2. Преобразовать `visibleBuildings` в draw data.
3. Использовать текущий `buildingRegistry.ts` для выбора sprite.
4. Сохранить selection/click behavior через hit areas или координатный picking.
5. Реализовать depth sorting.
6. Оставить DOM fallback за feature flag на время миграции.
7. Проверить карту на desktop/mobile viewport.

Результат:

- здания массово рисуются через Pixi;
- React больше не создает DOM-узел на каждую постройку;
- визуально карта остается совместимой с текущими PNG.

## Фаза 5. Добавить Overlay-Анимации Построек

Цель: оживить здания без дорогого GLB runtime.

Задачи:

1. Добавить overlay container поверх base building sprites.
2. Реализовать `animationClock`.
3. Подключить shared overlays: smoke, fire, sparks, ready marker.
4. Добавить phase offset по `building.id`.
5. Отключать неважные overlays на дальнем zoom.
6. Добавить mapping production/combat/construction state -> overlay list.
7. Покрыть frame selection тестами.

Результат:

- здания получают дешевые визуальные эффекты;
- анимации не вызывают React rerender;
- одинаковые объекты не двигаются синхронно.

## Фаза 6. Перенести Монстров В Animated Pixi Sprites

Цель: заменить DOM-классы монстров на полноценные atlas-анимации.

Задачи:

1. Добавить `monsterAssetRegistry`.
2. Сделать mapping monster state -> animation key.
3. Определять направление по движению или цели.
4. Реализовать interpolation между server positions, если backend отправляет движение дискретно.
5. Добавить health bars в Pixi overlay или ограниченный DOM layer.
6. Добавить fallback sprite/class для монстров без atlas.
7. Проверить idle/walk/attack/hit/death transitions.

Результат:

- монстры читаемо двигаются и атакуют;
- нет DOM-элемента на каждого монстра;
- fallback сохраняет работу старых типов.

## Фаза 7. Перенести Ресурсы, Дороги И Стены

Цель: довести массовый слой карты до единой Pixi-модели.

Задачи:

1. Перенести resource nodes в object layer.
2. Перенести shape-based roads/walls в object layer.
3. Сохранить существующий shape lookup.
4. Добавить contested/claimed/depleted overlays для ресурсов.
5. Проверить depth sorting дорог, стен, зданий и монстров.

Результат:

- все массовые объекты карты проходят через один renderer;
- DOM остается для UI, не для игрового мира.

## Фаза 8. GLB Preview Вместо GLB Map Runtime

Цель: оставить 3D там, где оно действительно полезно.

Задачи:

1. Перенести GLB-отображение в инспектор объекта и asset debug panel.
2. Ограничить количество активных Three renderers.
3. Добавить lazy loading GLB только при открытом preview.
4. Добавить clear lifecycle и dispose checks.
5. Убрать автоматическое использование GLB для массовых объектов карты.

Результат:

- GLB остается частью качества ассетов;
- карта не зависит от большого числа WebGL renderers.

## Фаза 9. Производительные Проверки

Цель: доказать, что архитектура держит нагрузку.

Задачи:

1. Добавить dev-сценарий с большим количеством fake buildings.
2. Добавить dev-сценарий с animated monsters.
3. Проверить FPS на desktop viewport.
4. Проверить память после pan/zoom и смены чанков.
5. Проверить отсутствие роста WebGL contexts.
6. Добавить Playwright smoke для nonblank Pixi canvas.
7. Зафиксировать базовые performance notes в документации.

Результат:

- можно уверенно наращивать количество объектов;
- regressions легче ловить до появления большой карты.

Реализация:

- dev-сценарии `?perf=buildings`, `?perf=monsters`, `?perf=mixed` генерируют fake-постройки, ресурсы, монстров и тайлы без записи в серверное состояние;
- `Performance HUD` показывает rolling FPS, видимые объекты, heap и активные Pixi/Three-контексты;
- smoke-контракт для nonblank Pixi canvas лежит в `frontend/tests/e2e/pixi-canvas.spec.ts`;
- методика ручной проверки зафиксирована в `docs/frontend/rendering-performance-notes.md`.

## Фаза 10. Удалить Старые DOM-Массовые Пути

Цель: завершить миграцию после стабилизации Pixi object layer.

Задачи:

1. Удалить feature flag DOM fallback, если Pixi path стабилен.
2. Упростить `IsoMap.tsx`.
3. Оставить React-компоненты только для UI и preview.
4. Обновить `docs/frontend/rendering-and-assets.md`.
5. Обновить тесты, которые завязаны на DOM-объекты карты.

Результат:

- архитектура карты становится цельной;
- новые анимированные ассеты добавляются через manifest и pipeline, а не через ручные React-компоненты.

Реализация:

- feature flag DOM fallback удален из `IsoMap.tsx`;
- постройки, ресурсы и монстры идут в `PixiStage`;
- React/DOM оставлен только для UI-оверлеев построек, HUD и preview/debug;
- неподдержанные manifest-ом постройки получают procedural Pixi fallback вместо исчезновения;
- рубка леса патчит Zustand и React Query cache сразу после клика/ответа сервера, чтобы тайл не откатывался к stale chunk data;
- `docs/frontend/rendering-and-assets.md` обновлен под финальную схему.

## Порядок Внедрения По Риску

Самый безопасный порядок:

1. Manifest types и registry fallback.
2. Blender/export contract и валидаторы.
3. Atlas loader без изменения текущей карты.
4. Pixi building layer за feature flag.
5. Overlay animations построек.
6. Animated monsters.
7. Resource/roads/walls migration.
8. GLB preview cleanup.
9. Performance scenarios.
10. Удаление DOM fallback.

Такой порядок позволяет проверять каждый шаг отдельно и не ломать текущую карту одним большим переписыванием.

## Критерии Готовности

Архитектуру можно считать внедренной, когда:

- массовые здания, ресурсы и монстры рисуются через Pixi object layer;
- atlas-based assets работают с fallback на старые PNG;
- postройки поддерживают overlay-анимации через manifest;
- монстры поддерживают atlas-анимации минимум для `idle`, `walk`, `attack`, `hit`, `death`;
- GLB используется только для preview/debug, а не для каждого объекта карты;
- дальний zoom отключает второстепенные анимации;
- React не rerenderится каждый animation frame;
- карта остается интерактивной при сотнях видимых объектов;
- есть тесты registry/state mapping/frame selection;
- есть smoke-проверка canvas-rendering.
