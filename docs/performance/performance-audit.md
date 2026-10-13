# Аудит Производительности И Оптимизации

Дата анализа: 2026-10-13.

Документ фиксирует текущее состояние производительности Real City, фактические узкие места, потенциальные риски роста и предложения по оптимизации. Анализ основан на чтении кода бэкенда, фронтенда, миграций, рендерера карты и текущих ассетов. Нагрузочные замеры в браузере и профилирование БД в рамках этого аудита не запускались, поэтому численные оценки являются инженерной оценкой по архитектуре и реализации.

## Краткая Оценка

| Часть | Оценка | Состояние |
| --- | ---: | --- |
| Бэкенд | 5/10 | Есть правильная доменная структура, индексы, очереди, `FOR UPDATE SKIP LOCKED`, chunk-модель и realtime-события. Основные риски: глобальные выборки в симуляции, последовательная генерация/загрузка чанков, несколько независимых пулов Postgres в одном процессе, in-memory лимитеры/идемпотентность по умолчанию, мало метрик производительности. |
| Фронтенд | 6/10 | Самый важный шаг уже сделан: массовые объекты карты вынесены в Pixi, есть viewport-фильтрация, dev performance-сценарии и HUD. Основные риски: Pixi-слои пересоздают и уничтожают sprites/graphics слишком часто, Zustand хранит массивы без индексов и делает O(n) upsert, realtime-события вызывают полную инвалидацию query-cache, публичные ассеты уже занимают около 1.1 GB. |

Текущий проект выглядит достаточно здоровым для прототипа и раннего вертикального среза. Для большого общего мира с сотнями игроков и тысячами объектов главные ограничения сейчас не в языке или библиотеках, а в алгоритмах выборки, батчинге, жизненном цикле рендер-объектов и управлении ассетами.

## Сильные Стороны

- Бэкенд разделен на domain/service/adapter/worker, что упрощает точечную оптимизацию без переписывания всей системы.
- Мир уже разбит на чанки, а API ограничивает радиус загрузки (`MaxChunkRadius`, `MaxViewportRadius`).
- В Postgres есть индексы для координат мира, построек, ресурсных узлов, монстров, очередей действий и outbox.
- Очередь `game_actions` использует `FOR UPDATE SKIP LOCKED`, что является хорошей базой для горизонтального масштабирования воркеров.
- Realtime уже фильтрует события по chunk/private/alliance-подпискам.
- Фронтенд использует Pixi для карты и оставляет DOM только для оверлеев.
- Есть dev-сценарии `?perf=...`, FPS/heap/GL HUD и тесты для части рендер-логики.

## Критичные И Приоритетные Проблемы

### P0/P1. Бэкенд: несколько независимых Postgres-pool в одном API-процессе

Файл: `backend/cmd/api/app.go`.

Сейчас `newApp` вызывает отдельные функции `buildStores`, `buildWorldStore`, `buildBuildingStore`, `buildEconomyStore`, `buildMonsterStore`, `buildActionStore`, `buildOutboxStore`, `buildUnitOfWork`. Каждая из них при наличии DSN вызывает `postgresadapter.Open(...)`, а `Open` создает `sql.DB` с `SetMaxOpenConns(20)`.

Последствие: один процесс может открыть до 7 независимых пулов по 20 соединений, то есть до 140 соединений к одной БД без учета других процессов. Это легко упрется в `max_connections`, усложнит наблюдаемость и создаст лишнюю конкуренцию за соединения.

Рекомендация:

- Открывать один `postgres.DB` в `newApp`.
- Передавать общий `*sql.DB` во все Postgres-репозитории и UnitOfWork.
- Закрывать pool при shutdown.
- Сделать настройки pool конфигурируемыми: `max_open_conns`, `max_idle_conns`, `conn_max_lifetime`.

Ожидаемый эффект: меньше соединений, стабильнее latency под нагрузкой, проще транзакции и диагностика БД.

### P0/P1. Бэкенд: MonsterAI читает всех монстров и делает N+1 запросы каждый tick

Файл: `backend/internal/worker/simulation/monster_ai.go`.

Фактический путь:

- `Tick` вызывает `ListByMap` и получает всех живых монстров карты.
- Затем для каждого монстра до `limit` делает `FindByID`.
- Внутри шага дополнительно вызывает `ListByChunk`, `ListByViewport`, `GetOrCreateChunk` для проверки проходимости.
- Движение может делать до 5 проверок проходимости на шаг.

Это нормально для десятков монстров, но плохо масштабируется на сотни и тысячи. При росте мира воркер будет регулярно читать глобальный набор, хотя обрабатывает только batch.

Рекомендация:

- Добавить репозиторный метод `ListActiveForTick(ctx, mapID, now, limit)` с индексом по `(map_id, state, updated_at)` или отдельным `next_tick_at`.
- Убрать `FindByID` на каждого монстра либо заменить на атомарный `UPDATE ... WHERE id = ... AND updated_at = ... RETURNING`, если нужна защита от гонок.
- Для проходимости кэшировать чанки на время одного tick: `map[ChunkCoord]Chunk`.
- Для поиска целей использовать spatial-запрос по окрестности, а не только текущий chunk и не полный набор.
- События монстров писать батчем либо только при реально изменившемся состоянии.

Ожидаемый эффект: tick монстров станет зависеть от `limit` и активной зоны, а не от размера всей карты.

### P0/P1. Бэкенд: MonsterSpawner многократно читает все постройки карты

Файл: `backend/internal/worker/simulation/monster_spawner.go`.

`Tick` получает всех живых монстров через `ListByMap`, а проверка безопасности spawn-точки в `spawnUnsafe` вызывает `buildings.ListByMap` для каждой проверяемой клетки. При релокации spawn-точки код может проходить кольца кандидатов и для каждого кандидата заново читать все постройки.

Последствие: сложность может стать `spawn_points * candidates * all_buildings`. Это один из самых опасных участков при росте числа построек.

Рекомендация:

- Заменить `ListByMap` на `ListByViewport/ListNearTile` для радиуса `monsterSpawnSafeRange`.
- В рамках одного tick один раз построить spatial-index занятых клеток вокруг проверяемых spawn-зон.
- Хранить `alive_count` по `spawn_id` в запросе или отдельном агрегате, а не читать всех монстров.
- Добавить SQL-метод `CountAliveBySpawn(mapID)` с `GROUP BY spawn_id`.

### P1. Фронтенд: PixiStage уничтожает и пересоздает объекты при каждом redraw

Файл: `frontend/src/game/renderer/PixiStage.tsx`.

В `drawStage` удаляются и уничтожаются все дети `terrainSprites`, `objectSprites`, `buildingAnimationOverlays`, затем они создаются заново. Отдельно `drawMonsterLayer` на каждом Pixi ticker удаляет все monster-children и снова создает контейнеры/graphics.

Это дает:

- постоянные allocations;
- давление на GC;
- скачки frame time;
- лишнюю работу GPU/renderer;
- особенно плохое поведение на сценариях с сотнями анимированных монстров.

Рекомендация:

- Ввести retained object layer: `Map<id, Sprite/Container>` для построек, ресурсов, монстров.
- При изменениях делать diff: add/update/remove, а не full rebuild.
- Для монстров обновлять `position`, `zIndex`, `alpha`, `texture/frame`, health-bar, но не уничтожать контейнер каждый кадр.
- Отдельно разделить статичный terrain-layer, object-layer и animated-overlay-layer.
- Terrain перерисовывать только при смене загруженных чанков, tile mutation или zoom threshold, а не при hover/selection/camera.
- Для часто повторяемых fallback Graphics рассмотреть `RenderTexture` или atlas/sprite frames.

Ожидаемый эффект: меньше GC, стабильнее FPS, возможность держать больше объектов без просадок.

### P1. Фронтенд: ассеты уже занимают около 1.1 GB

Факты на момент аудита:

- `frontend/public/assets`: около 1.1 GB.
- Файлов в `frontend/public/assets`: 3484.
- Пример крупных файлов: `glass_workshop_levels.glb` около 22 MB, `clay_quarry_levels.glb` около 19 MB, `mine_levels.glb` около 18 MB, `sand_quarry_levels.glb` около 16 MB.
- В `frontend/dist` также около 1.1 GB, то есть публичные ассеты копируются в сборку.

Это критично для веб-игры: деплой, CDN, cold start, кеширование, локальная разработка и браузерная загрузка будут тяжелыми. Даже если карта сейчас использует PNG-спрайты, наличие большого массива GLB в public ухудшает размер сборки.

Рекомендация:

- Разделить runtime-ассеты и source/review/dev-ассеты.
- Убрать contact sheets, review PNG, исходные/уровневые GLB из `public`, если они не загружаются клиентом в игре.
- Ввести manifest runtime-ассетов с LOD и lazy-loading.
- Для GLB: Draco/Meshopt compression, texture compression, decimation, split по уровням и состояниям.
- Для 2D карты: собирать PNG в texture atlases, лучше с WebP/AVIF вариантами там, где допустимо.
- Добавить CI-проверку asset budget: общий размер runtime-assets, максимальный размер файла, количество файлов.

## Бэкенд: Подробные Наблюдения

### Чанки мира загружаются и создаются последовательно

Файл: `backend/internal/adapter/postgres/world_repo.go`.

`GetOrCreateChunks` просто проходит координаты циклом и вызывает `GetOrCreateChunk`. На радиусе 3 это до 49 чанков, каждый chunk делает отдельный `SELECT world_chunks`, затем отдельный `SELECT world_tiles`, а при miss еще 100 отдельных `INSERT` для тайлов, потому что размер чанка сейчас 10.

Рекомендация:

- Для чтения пачки чанков сделать batch-query по `(chunk_x, chunk_y)` и одним запросом загрузить все tiles.
- Для генерации использовать bulk insert: `COPY`, multi-row `INSERT` или `pq.CopyIn`.
- Убрать повторный `ensureMap` из каждого chunk-вызова, выполнять один раз при bootstrap или на первом запросе.
- При race на создание чанка после `ON CONFLICT DO NOTHING` перечитывать уже созданный чанк без ошибки.

### Проверка размещения построек делает несколько последовательных запросов

Файл: `backend/internal/service/building.go`.

Размещение вызывает:

- загрузку чанка для origin tile;
- загрузку чанков для footprint;
- `ListByPlayer`;
- `existingBuildingsForFootprint`, который читает buildings по chunk;
- проверку монстров по viewport;
- расход ресурсов;
- создание building;
- иногда добавление action.

Это приемлемо для одиночного действия, но при активной стройке будет чувствительно к latency БД.

Рекомендация:

- Добавить специализированный запрос `ListBuildingsIntersectingFootprint(mapID, minX, minY, maxX, maxY)`.
- Проверку лимита построек делать агрегатом или cached player city stats, а не полным списком построек игрока.
- Вынести размещение в UnitOfWork, чтобы списание ресурсов и создание постройки были атомарны.
- Добавить уникальные/исключающие ограничения на занятые клетки. Для footprint больше 1x1 можно хранить `building_occupied_tiles(map_id, tile_x, tile_y, building_id)` с PK `(map_id, tile_x, tile_y)`.

### Симуляция производств и действий имеет хорошую базу, но дублирует механизмы

Есть `game_actions`, `ListDue` для построек и `ListDueProductionJobs`. При этом completion может идти и через action queue, и через отдельные due-сканеры.

Рекомендация:

- Определить единый источник правды: либо все таймеры идут через `game_actions`, либо due-сканеры являются fallback/repair.
- Если оставлять оба механизма, добавить защиту от двойной обработки через идемпотентные state transitions.
- Собирать метрики по каждому типу tick отдельно: fetched, processed, failed, duration, lag oldest_due.

### EventBus и WebSocket фильтрация линейны по числу клиентов

Файлы: `backend/internal/service/eventbus.go`, `backend/internal/adapter/ws/gateway.go`.

`EventBus.Publish` отправляет событие всем подписчикам event bus, а gateway затем проходит по всем соединениям и проверяет `Matches`. Это нормально для десятков/сотен клиентов, но при большом онлайне лучше индексировать подписки.

Рекомендация:

- В gateway хранить индексы `chunkID -> connections`, `playerID -> connections`, `alliance -> connections`.
- При подписке/отписке обновлять индексы.
- На publish отправлять только целевым наборам соединений.
- Добавить счетчики dropped messages, queue full disconnects, active connections, subscribed chunks.

### In-memory idempotency и rate limit по умолчанию не подходят для нескольких API-инстансов

Файлы: `backend/internal/adapter/http/middleware/idempotency.go`, `backend/internal/adapter/http/middleware/ratelimit.go`.

В коде есть Redis-адаптеры, но router создается с `nil`, значит используются in-memory реализации. При нескольких API-инстансах idempotency и rate limit будут локальными для процесса.

Рекомендация:

- Подключить Redis idempotency/rate-limit store из конфигурации.
- Сделать in-memory только dev fallback.
- Добавить периодическую очистку expired records в memory-store, чтобы dev-сервер не копил ключи бесконечно.

### Метрики пока слишком бедные

`/metrics` сейчас возвращает только `real_city_http_ready 1`. Для оптимизации общего мира нужны рабочие метрики.

Рекомендация добавить:

- latency HTTP по route/method/status;
- DB query duration хотя бы вокруг репозиториев hot path;
- simulation tick duration по подсистемам;
- action/outbox lag и retries;
- active websocket connections и dropped messages;
- chunk load/create counters;
- размер batches и количество объектов в ответах.

## Фронтенд: Подробные Наблюдения

### Zustand-store использует массивы и O(n) upsert

Файл: `frontend/src/game/state/useGameStore.ts`.

`addBuilding`, `upsertResourceNode`, `upsertMonster`, `updateWorldTile` фильтруют или map-ят массивы. Для небольшого числа объектов это просто и удобно. Для тысяч объектов realtime-события будут часто копировать большие массивы и триггерить пересчеты memo.

Рекомендация:

- Хранить normalized state: `buildingsById`, `resourcesById`, `monstersById`, `tilesByKey`.
- Для рендера иметь memoized selectors, возвращающие массив только для видимой зоны.
- Не менять `selectedBuildingId` и `selectedTile` внутри `addBuilding` при каждом realtime update; это сейчас может сдвигать UI-selection на чужие события.
- Для tile lookup при клике заменить `mapTiles.find(...)` на `tilesByKey.get(...)`.

### Realtime-события слишком часто инвалидируют React Query

Файл: `frontend/src/features/world/realtime.ts`.

После точечного применения события в Zustand код дополнительно вызывает `invalidateQueries` для `world`, `buildings`, `resources`, `monsters`, `inventory`. Для realtime-потока это может привести к лишним HTTP-запросам и постоянной замене массивов.

Рекомендация:

- Для событий мира патчить query-cache точечно (`setQueriesData`) вместо полной инвалидации.
- Для монстров не инвалидировать `['monsters']` на каждое движение; поллинг оставить как reconciliation fallback.
- Инвентарь инвалидировать только для событий, где payload реально меняет инвентарь, либо присылать inventory delta.
- Добавить debounce/batch invalidation, если полная синхронизация все же нужна.

### Viewport/chunk radius рассинхронизирован

В `IsoMap` chunk-загрузка всегда идет через `useVisibleChunks(centerChunk, 1)`, а realtime подписка берет `viewport.radius` и ограничивает его до 1..4. Монстры загружаются по `viewport.radius * 48`. Это может приводить к ситуации, где realtime и monsters видят больше мира, чем загруженные tiles/building layer.

Рекомендация:

- Ввести единый `visibleWorldWindow`: chunk radius, tile radius, pixel bounds.
- Использовать его для world chunks, buildings/resources/monsters, realtime subscribe.
- Менять радиус от zoom/stage size, а не держать константы в разных местах.

### Рендер карты уже фильтрует объекты, но terrain все еще пересобирается

`filterVisibleMapObjects` отсекает здания/ресурсы/монстров по экрану. Это хорошо. Но `drawStage` пересобирает terrain sprites при изменении camera, hover, selection, monsters, buildings.

Рекомендация:

- Разделить draw-процессы:
  - camera transform: менять transform контейнеров;
  - selection/hover: перерисовывать только overlay graphics;
  - monsters: обновлять только monster-layer;
  - terrain: пересоздавать только при смене tiles или terrain texture set.
- В Pixi использовать контейнерный transform вместо пересчета каждой позиции при каждом pan, если wrapping логика позволяет.

### DOM-оверлеи поверх карты могут стать bottleneck

Сейчас DOM используется для строительных таймеров и work badges по видимым зданиям. Это приемлемо, но при сотнях видимых production/field overlays DOM начнет конкурировать с Pixi.

Рекомендация:

- Ограничить DOM-оверлеи только выбранным объектом, hover и небольшим числом важных ready-состояний.
- Остальные статусы рисовать в Pixi overlay layer.
- Для таймеров обновлять текст раз в секунду и только для видимых/важных объектов.

### Сборка и ассеты требуют budget-политики

Vite-конфиг минимален и не задает chunking/budget. Public assets копируются как есть.

Рекомендация:

- Добавить скрипт проверки размера `frontend/public/assets/runtime`.
- Разделить `public/assets/runtime` и `tools/assets/output`/`docs/assets`.
- Настроить manual chunks для крупных библиотек (`pixi.js`, `three`, react vendor) после анализа bundle.
- Подключить bundle visualizer для периодической диагностики.

## Предлагаемый План Оптимизации

### Этап 1. Быстрые Архитектурные Исправления

1. Перевести API на один общий Postgres pool.
2. Подключить Redis для idempotency/rate-limit в non-dev окружении.
3. Добавить базовые метрики simulation/http/ws/db.
4. Вынести runtime-ассеты из общего массива public и ввести asset budget.

### Этап 2. Горячие Пути Бэкенда

1. Переписать MonsterSpawner без `ListByMap` внутри `spawnUnsafe`.
2. Переписать MonsterAI на `ListActiveForTick` и chunk cache внутри tick.
3. Добавить batch load/create для world chunks.
4. Оптимизировать размещение построек через footprint/intersection queries и транзакцию.

### Этап 3. Горячие Пути Фронтенда

1. Перевести Pixi object layer на retained sprites/containers.
2. Разделить terrain/object/monster/overlay redraw.
3. Нормализовать Zustand-store и убрать O(n) upsert для realtime событий.
4. Заменить realtime invalidation на точечные cache patches и throttled reconciliation.

### Этап 4. Нагрузочная Проверка

1. Запустить frontend perf-сценарии:
   - `?perf=buildings&perfBuildings=2600`
   - `?perf=monsters&perfMonsters=720`
   - `?perf=mixed&perfBuildings=2600&perfMonsters=720&perfResources=260`
2. Добавить backend seed/load script:
   - 10k buildings;
   - 5k resource nodes;
   - 1k active monsters;
   - 100 concurrent websocket clients;
   - 50 players doing build/harvest/attack actions.
3. Снимать p50/p95/p99 HTTP latency, simulation tick duration, DB query time, FPS, heap, dropped ws messages.

## Целевые Критерии

Для ближайшего playable alpha:

- Backend p95 для чтения viewport/chunks: до 150 ms на локальной/тестовой БД.
- Backend simulation tick: стабильно меньше tick interval, без накопления backlog.
- WebSocket dropped messages: 0 в нормальном сценарии.
- Frontend desktop: 50-60 FPS на обычной карте, не ниже 30 FPS в stress-сценарии.
- Frontend heap после 5 минут pan/zoom/realtime: стабилизируется, не растет монотонно.
- Runtime assets initial route: загружает только нужный минимум, без скачивания крупных GLB для объектов вне экрана.

## Итог

Главный риск бэкенда сейчас - не отсутствие индексов, а глобальные выборки и повторяющиеся запросы в симуляции. Главный риск фронтенда - не React сам по себе, а пересоздание Pixi-объектов и неуправляемый рост ассетов. Исправления хорошо ложатся на текущую архитектуру: систему не нужно переписывать, но нужно заменить несколько прототипных решений на retained rendering, batch/spatial queries и централизованное управление ресурсами.
