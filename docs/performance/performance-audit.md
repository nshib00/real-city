# Аудит Производительности И Оптимизации

Дата исходного повторного анализа: 2026-10-14. Полный срез, дальнейшая проверка и итоги оптимизации от 01.11.2026 приведены в конце документа. Оценки и численные значения в предыдущих разделах сохранены как история соответствующих дат; текущие оценки: **фронтенд 7,0/10 (предварительно), бэкенд 7,0/10**.

Документ обновлен после очередного анализа загрузки ассетов, чанков, realtime-подписок и viewport-запросов. Анализ основан на повторном чтении frontend hot-path карты, React Query cache, Pixi renderer, WebSocket subscriptions, backend world repository и существующих тестах. Полное нагрузочное тестирование, Chrome Performance, WebGL frame capture и `EXPLAIN ANALYZE` для Postgres в рамках этого повторного аудита не запускались, поэтому численные оценки ниже являются инженерной оценкой по архитектуре, коду и тестовой проверке.

## Краткая Оценка

| Часть | Оценка | Состояние |
| --- | ---: | --- |
| Бэкенд | 8.5/10 | Стало заметно лучше: API использует один общий Postgres pool, чанки загружаются batch-запросами, создание tiles переведено на `COPY`, горячие world chunks кэшируются в `WorldRepo` и патчатся при `UpdateTile`, MonsterAI больше не читает всех монстров карты, MonsterSpawner считает живых монстров агрегатом, WebSocket gateway маршрутизирует события через индексы подписок, `/metrics` показывает HTTP/WS и DB показатели, а размещение построек больше не читает все здания игрока ради лимита. Главные оставшиеся риски: in-memory rate limit/idempotency, последовательное создание отсутствующих чанков, отсутствие simulation tick/backlog metrics, не полностью атомарные игровые действия и отсутствие claim/lock для части simulation flows. |
| Фронтенд | 8.6/10 | Основные прототипные bottleneck-и карты закрыты: realtime-события патчат query-cache, радиус чанков синхронизирован с backend limit `1..3`, world chunks держатся в React Query cache дольше, monster/threat queries и WS subscriptions больше не пересобираются на каждый шаг drag внутри chunk, Zustand хранит индексы для hot-path upsert/select/delete, tile lookup при клике стал `Map`, массовые объекты рисуются через Pixi, terrain/building/resource/overlay слои стали retained по ключам, GLB исключены из production runtime, runtime asset budget держится около `210.1 MB`, а основной app chunk держится около `220.6 kB`. Главные оставшиеся риски: большие коллекции все еще отдаются компонентам массивами, часть DOM-оверлеев может стать узким местом при сотнях производств, Pixi `vendor` chunk остается крупным, нет браузерного профилирования на реальном stress-сценарии. |

Проект уже выглядит достаточно крепко для ранней playable alpha и локального stress-тестирования. До масштабирования на большой общий мир нужно нормализовать клиентское состояние, добавить tick/backlog метрики worker и подтвердить гипотезы нагрузочным профилированием на stress-сценариях.

## Что Уже Улучшено

### Бэкенд

- `backend/cmd/api/app.go`: API теперь открывает один `postgresadapter.DB` и передает общий `*sql.DB` во все Postgres-репозитории и UnitOfWork. Риск множества независимых пулов в одном API-процессе снят.
- `backend/internal/adapter/postgres/world_repo.go`: `GetOrCreateChunks` теперь сначала делает batch-загрузку существующих чанков и tiles через `findChunks`, создание tiles в `createChunk` использует `pq.CopyIn`, горячие chunks кэшируются in-memory, а `UpdateTile` патчит cached chunk после изменения тайла.
- `backend/internal/worker/simulation/monster_ai.go`: MonsterAI использует `ListActiveForTick` вместо чтения всех монстров карты и держит cache чанков в рамках tick.
- `backend/internal/adapter/postgres/monster_repo.go`: добавлены `ListActiveForTick` и `CountAliveBySpawn`.
- `backend/internal/worker/simulation/monster_spawner.go`: Spawner больше не читает все постройки карты для каждой spawn-точки; используется `ListByViewport` вокруг кандидата и агрегированный `CountAliveBySpawn`.
- `backend/internal/adapter/ws/gateway.go`: WebSocket fan-out идет через индексы `chunkID -> connections`, `playerID -> private connections`, `alliance -> connections`; на событие собирается только целевой набор подключений.
- `backend/internal/adapter/http/middleware/metrics.go`, `backend/internal/adapter/http/metrics.go`: `/metrics` теперь отдает in-process HTTP counters/sums по route/method/status class и WebSocket gauges/counters: connections, subscriptions, events, fanout, drops.
- `backend/internal/service/building.go`, `backend/internal/adapter/postgres/building_repo.go`: placement больше не вызывает полный `ListByPlayer` для проверки лимита и ратуши; добавлен агрегатный `PlayerPlacementStats`.
- `backend/db/migrations/000018_performance_indexes.sql`: добавлены индексы для tick монстров, живых монстров по spawn, viewport построек и owner/type/state статистики размещения.
- Проверка после исправлений: `GOCACHE=/tmp/real-city-go-build-cache go test ./internal/adapter/postgres ./internal/service ./internal/adapter/http/handler` в `backend` проходит.

### Фронтенд

- `frontend/src/features/world/realtime.ts`: realtime-события теперь точечно патчат React Query cache через `setQueryData`/`setQueriesData`, а не делают массовую инвалидацию `world/buildings/resources/monsters/inventory` на каждое событие; подписки на chunks пересобираются по chunk center/radius, а не по каждому изменению `viewport.center`.
- `frontend/src/features/world/useVisibleChunks.ts`: world chunks получили отдельные `staleTime`/`gcTime`, поэтому повторная прокрутка по уже виденной зоне чаще берет данные из React Query cache.
- `frontend/src/features/monster/MonsterSync.tsx`, `frontend/src/features/threat/ThreatPanel.tsx`: запросы монстров и угроз привязаны к chunk center, а не к точному tile center, поэтому drag внутри одного chunk больше не создает новый query key каждый кадр.
- `frontend/src/game/state/useGameStore.ts`: `addBuilding`, `upsertResourceNode`, `upsertMonster`, `updateWorldTile` больше не делают лишние побочные действия; store поддерживает `buildingIndexById`, `resourceNodeIndexById`, `monsterIndexById`, `worldTileIndexByKey`, поэтому hot-path select/upsert/delete больше не начинается с полного сканирования массива.
- `frontend/src/game/IsoMap.tsx`: радиус видимых чанков вычисляется от размера stage и zoom; realtime viewport radius синхронизируется с тем же значением; поиск tile при клике идет через `Map`.
- `frontend/src/game/IsoMap.tsx`, `frontend/src/features/production/ProductionPanel.tsx`: статичные production recipes получили повышенный `staleTime`/`gcTime`; occupied tiles для карты считаются по `visibleBuildings`, а не по всем зданиям мира.
- `frontend/src/game/renderer/PixiStage.tsx`: монстры вынесены в отдельный слой; terrain sprites, building sprites/fallbacks, resource containers и building animation overlays сохраняются между redraw по ключам и удаляются только когда объект исчез из видимой области.
- `frontend/src/game/renderers/buildingRegistry.ts`: production build больше не glob-ит `frontend/src/assets/buildings/**/*.glb`; GLB остаются dev/test preview-путем, но не тянут тяжелые модели в production runtime.
- `frontend/vite.config.ts`: production build удаляет non-runtime ассеты из `dist/assets`: `.blend`, `.blend1`, `.glb`, backup, review, preview, contact sheets; настроены vendor chunks для React, Query, Pixi, Three preview.
- `frontend/scripts/check-asset-budget.mjs`: runtime asset budget исключает source/preview/GLB ассеты.
- Текущий `npm run assets:budget` проходит с результатом `210.1 MB` runtime assets across `2035` files.
- Текущий production build проходит; фактический `frontend/dist/assets` после pruning не содержит `.glb`. Крупнейшие JS chunks: `vendor-pixi` `516.8 kB`, lazy `vendor-three-preview` `777.8 kB`, основной `index` `220.6 kB`, `vendor-react` `193.8 kB`.
- Проверка после исправлений: targeted Vitest по карте/world/store проходит, `npm run lint` и `npm run build` проходят.

## Оставшиеся P0/P1 Риски

### P1. Фронтенд: состояние карты частично индексировано, но еще не полностью нормализовано

Файл: `frontend/src/game/state/useGameStore.ts`.

Статус: частично исправлено.

Store теперь держит индексы `id/key -> position` для зданий, ресурсных узлов, монстров и world tiles. Это убирает линейный поиск из горячих операций `selectаваBuilding`, `selectMonster`, `addBuilding`, `upsertResourceNode`, `upsertMonster`, `deleteBuilding`, `setWorldTiles`/`updateWorldTile`. Для частых realtime patch это дешевле прежнего `findIndex` по массиву.

Оставшаяся проблема: публичные коллекции все еще хранятся и отдаются компонентам массивами. При каждом upsert меняется ссылка на массив, а крупные derived selectors в `IsoMap` могут пересчитываться целиком. Для сотен объектов это нормально; для тысяч realtime-событий в минуту следующей ступенью нужна полноценная нормализация и spatial-index.

Рекомендации:

- Перейти от positional index к normalized state: `buildingsById`, `resourceNodesById`, `monstersById`, `worldTilesByKey`.
- Для рендера формировать массивы через memoized selectors только для видимой зоны.
- Хранить spatial-index по chunk/tile: например `buildingIdsByChunk`, `resourceIdsByChunk`, `monsterIdsByChunk`.
- Для `worldTiles` следующим шагом держать canonical `tilesByKey`, чтобы patch вообще не требовал clone большого массива до момента формирования render slice.

### P1. Фронтенд: требуется браузерное профилирование retained Pixi path

Файл: `frontend/src/game/renderer/PixiStage.tsx`.

Статус: исправлено архитектурно, но требует подтверждения профилированием.

`drawStage` больше не делает массовые `removeChildren()`/destroy для terrain, buildings, resources и building overlays на каждый redraw. Вместо этого слой держит:

- `terrainSpriteCache` по `tileKey`;
- `buildingSpriteCache` по `building.id`;
- `resourceSpriteCache` по `resource.id`;
- `buildingOverlayCache` по `buildingId:overlayKey`;
- отдельный retained monster layer.

Оставшийся риск не в полном пересоздании Pixi children, а в том, что при изменении камеры все еще пересчитываются видимые tiles/objects, hit areas и позиции. Это дешевле прежнего create/destroy path, но на больших viewport нужно измерить frame time, GC и количество children.

Рекомендации:

- Добавить dev-счетчики Pixi children по слоям, cache size, created/destroyed per redraw.
- Разделить camera transform и object diff, если профилирование покажет дорогой pan/zoom.
- Перерисовывать terrain только при изменении набора tiles, terrain texture set или существенном изменении видимого окна.
- Для fallback Graphics рассмотреть `RenderTexture`/texture atlas, если fallback-построек станет много.

Ожидаемый эффект от уже внесенной правки: меньше allocation/GC при pan/zoom/hover/selection и стабильнее FPS в stress-сценариях с большим количеством видимых объектов.

### P1. Бэкенд: observability все еще неполная

Инвентаризация сигналов, исходный синтетический срез `/metrics` и матрица диагностики находятся в [каталоге метрик](../operations/metrics-catalog.md) и [руководстве по наблюдаемости](../operations/observability.md). В фазе 2 [плана наблюдаемости](../plans/observability-plan.md) исправлена разбивка HTTP по шаблонам маршрутов; в фазе 3 добавлены DB pool stats, duration горячих операций, cache и этапов размещения; в фазе 4 — длительность tick/этапов и снимки очередей; в фазе 5 — dashboards и предварительные правила оповещений. Фаза 6 добавляет frame p50/p95, visible objects, Pixi children/cache/churn в dev HUD и [протокол браузерного профилирования](browser-profiling.md) с сопоставлением по времени с серверными графиками. В фазе 7 получена [локальная серверная базовая линия](observability-baseline.md); браузерные прогоны и проверка порогов на реалистичной игровой нагрузке остаются открытыми.

Файл: `backend/internal/adapter/http/router.go`.

Статус: HTTP, WebSocket, Postgres hot path, tick и backlog worker измеряются; baseline под реальной нагрузкой остается задачей фазы 7.

`/metrics` API отдает HTTP histogram по route/method/status class, WebSocket counters/gauges, DB pool stats, именованные операции Postgres, cache и этапы размещения. Самостоятельный worker отдает свой DB pool и runtime через внутренний listener. Это позволяет отличить рост SQL p95 от ожидания соединения и от CPU-генерации чанков.

Оставшаяся проблема: пороги алертов и цена агрегатных запросов очередей не подтверждены под реальной нагрузкой; EventBus самостоятельного worker пока не транслирует события в процесс API.

Рекомендации:

- Сопоставить новые DB/world/placement ряды с HTTP p95 и проверить планы горячих SQL на тестовых данных по runbook.
- Simulation tick duration/processed/failed/lag по подсистемам.
- Outbox/action queue lag: oldest due, fetched, processed, retries.
- WebSocket metrics дополнить slow consumers / queue depth histogram, если появятся долгоживущие очереди.
- Frontend perf telemetry для dev/staging: FPS, heap, visible objects, Pixi object counts.

## Бэкенд: Подробные Наблюдения

### Postgres pool

Статус: исправлено для API.

`newApp` вызывает `openPostgres` один раз и передает общий pool во все Postgres-репозитории. Pool закрывается в `app.run`. Это снимает прежний риск 7 независимых pool по 20 соединений в одном процессе.

Оставшееся улучшение:

- Сделать параметры pool конфигурируемыми: `max_open_conns`, `max_idle_conns`, `conn_max_lifetime`.
- Учитывать отдельный pool worker-процесса (`backend/cmd/worker/main.go`) при расчете лимитов Postgres.

### World chunks

Статус: частично исправлено.

`GetOrCreateChunks` теперь делает batch-чтение существующих чанков и tiles через bounding box, а tiles при создании чанка пишутся через `pq.CopyIn`. Повторные обращения к уже загруженным chunks проходят через in-memory cache внутри `WorldRepo`; при `UpdateTile` cached chunk патчится, поэтому рубка леса не должна возвращать старое состояние из серверного кэша.

Оставшиеся риски:

- Отсутствующие чанки по-прежнему создаются последовательно.
- `findChunks` читает tiles по bounding box и затем фильтрует wanted chunks в Go. Для обычного квадратного радиуса это нормально, но для разреженного набора координат может читать лишние tiles.
- `ensureMap` все еще вызывается часто, хотя `ON CONFLICT DO NOTHING` делает это безопасным.
- In-memory chunk cache является process-local. Для нескольких API-инстансов нужны sticky sessions, внешний cache/pubsub invalidation или отказ от межпроцессного cache.

Рекомендации:

- Для пачки missing chunks создавать их в одной транзакции.
- Для разреженных наборов рассмотреть join через `VALUES (chunk_x, chunk_y)` вместо bounding box.
- Кэшировать факт ensureMap на уровне repo/process или выполнять bootstrap отдельно.

### MonsterAI

Статус: существенно улучшено.

`Tick` использует `ListActiveForTick(ctx, mapID, limit)`, а не `ListByMap`. Это привязывает работу tick к batch size, а не ко всем монстрам карты. Внутри tick есть cache чанков для `isPassable`.

Оставшиеся риски:

- `ListActiveForTick` сортирует по `updated_at`, но нет `next_tick_at`; монстры с разной скоростью/состоянием могут обрабатываться слишком часто или неравномерно.
- `nearestTarget` ищет цель только в текущем chunk через `ListByChunk`, а не по aggro radius; это дешево, но может быть игровым и performance-компромиссом.
- Каждый обновленный монстр пишет `Update`, `AddEvent`, публикует событие и логирует tick. При больших batch логирование станет заметным.
- Нет атомарного claim/lock для монстров в `ListActiveForTick`, поэтому при нескольких worker-процессах возможна двойная обработка.

Рекомендации:

- Добавить `next_tick_at` или `locked_until` для монстров и claim через `FOR UPDATE SKIP LOCKED`.
- Логировать monster tick sampling-ом или на debug-уровне.
- Писать события батчем либо коалесцировать movement-события.
- Использовать spatial-запрос по aggro radius, если gameplay требует видеть цели вне текущего chunk.

### MonsterSpawner

Статус: существенно улучшено.

`CountAliveBySpawn` заменил чтение всех живых монстров, а `spawnUnsafe` проверяет только viewport вокруг кандидата. Индексы для spawn и viewport добавлены.

Оставшиеся риски:

- `relocateIfUnsafe` может многократно вызывать `spawnUnsafe`, а каждый вызов отдельно читает chunk и nearby buildings.
- `tilePassable` не использует cache чанков, в отличие от MonsterAI.
- При большом количестве spawn points или частых relocation затраты снова станут заметными.

Рекомендации:

- Добавить cache чанков и nearby buildings на время одного spawner tick.
- Для ring-поиска предварительно загрузить bounding viewport построек вокруг всей зоны поиска.
- Сохранять relocated spawn только при реальном изменении координат и считать relocation attempts метрикой.

### WebSocket fan-out

Статус: исправлено на уровне gateway.

`backend/internal/adapter/ws/gateway.go` больше не проходит по всем WebSocket-соединениям для каждого targeted event. При `subscribe/unsubscribe` gateway обновляет индексы:

- `chunkSubs`: подписки на чанки;
- `privateSubs`: приватные события игрока;
- `allianceSubs`: alliance-каналы.

При публикации события gateway собирает union только из релевантных индексов. Глобальные события без `chunkID`, `playerID` и `alliance` по-прежнему рассылаются всем соединениям, что соответствует их семантике. Добавлены счетчики `eventsSent`, `fanoutTotal`, `drops` и gauges подписок/соединений для `/metrics`.

Оставшиеся риски:

- `EventBus.Publish` все еще рассылает событие всем подписчикам самого event bus. В текущей архитектуре это обычно один gateway внутри процесса, поэтому риск ниже, чем прежний scan всех WS clients. Если появятся несколько локальных подписчиков с разными интересами, bus тоже стоит индексировать или разделить по topic.
- Индексы живут in-memory внутри API-инстанса. Для multi-instance WebSocket нужны sticky sessions или внешний pub/sub слой.
- Нет histogram-а queue depth / slow consumers; сейчас видны только drops.

### Размещение построек

Файл: `backend/internal/service/building.go`.

Статус: частично исправлено.

Размещение построек все еще выполняет несколько последовательных операций: проверка мира/footprint, поиск пересечений, проверка монстров viewport, списание ресурсов, создание building, постановка action. Но один старый горячий участок закрыт: вместо полного `ListByPlayer` для проверки ратуши и лимита теперь используется `PlayerPlacementStats`, который агрегирует `town_hall_level` и `used_limit` в Postgres. Для этого добавлен индекс `idx_buildings_owner_limit_stats`.

Также добавлен явный метод `ListIntersectingFootprint`, пока реализованный тем же overlap-запросом, что и viewport. Это фиксирует контракт hot-path и упрощает дальнейшую замену на таблицу occupied tiles или специализированный SQL.

Рекомендации:

- Перевести размещение в UnitOfWork: списание ресурсов, создание building, action queue.
- Для предотвращения коллизий хранить `building_occupied_tiles(map_id, tile_x, tile_y, building_id)` с PK `(map_id, tile_x, tile_y)`.
- Добавить DB duration metric для `PlayerPlacementStats`, footprint intersection и create building.

### Таймеры, actions и production

Статус: база хорошая, но механизмы раздвоены.

`game_actions` и `outbox_events` используют `FOR UPDATE SKIP LOCKED`, что хорошо для воркеров. При этом часть due-логики также живет в отдельных сервисах production/buildings/fields.

Рекомендации:

- Зафиксировать единый источник правды для таймеров: все через `game_actions` или due-сканеры только как repair/fallback.
- Добавить идемпотентные state transitions для защиты от двойной обработки.
- В метрики вынести lag oldest due и количество processed/failed по типу action.

### Rate limit и idempotency

Файлы: `backend/internal/adapter/http/router.go`, `backend/internal/adapter/http/middleware/*`.

Статус: остается проблемой для multi-instance.

Router создает `middleware.RateLimit(nil, ...)` и `middleware.Idempotency(nil, ...)`, то есть используются in-memory реализации. Они не синхронизируются между API-инстансами и могут копить ключи в памяти dev/prod процесса.

Рекомендации:

- Подключить Redis/Postgres-backed store для non-dev окружений.
- Оставить in-memory только explicit dev fallback.
- Добавить очистку expired idempotency records и rate-limit buckets.

## Фронтенд: Подробные Наблюдения

### Realtime и React Query

Статус: исправлено для основного realtime-потока.

`applyRealtimeEvent` патчит cache точечно:

- `world.tile.changed` -> `['world', 'chunks']`;
- building placed/updated/removed -> `['buildings']`;
- resource changed -> `['resources', 'nodes']`;
- monster events -> `['monsters']`.

Это снимает старый риск сетевого шторма от `invalidateQueries` на каждое realtime-событие.

Оставшиеся замечания:

- В локальных mutations (`IsoMap`, `BuildMenu`, `Inspector`, `ProductionPanel`) invalidation остается нормальным и в целом уместным, но часть мест можно заменить прямым patch при необходимости.
- Для движения монстров cache patch все еще сканирует массив query результата через `findIndex`; это нормально как промежуточный этап, но normalized cache станет лучше.

### Viewport/chunk radius

Статус: исправлено частично.

`IsoMap` вычисляет `visibleChunkRadius` от `stageSize` и `camera.zoom`, использует его в `useVisibleChunks`, а `viewport.radius` синхронизируется с этим значением для realtime-подписок. Radius теперь ограничен `1..3`, как backend `MaxChunkRadius`, чтобы широкий viewport/низкий zoom не приводил к невалидным запросам `radius=4`.

Запросы монстров, угроз и WebSocket chunk subscriptions теперь используют chunk center/radius. Это уменьшает сетевую и React Query churn-нагрузку при прокрутке: движение внутри текущего chunk больше не меняет query key и не отправляет повторную подписку на тот же набор chunks.

Оставшиеся риски:

- Монстры и объекты все еще фильтруются из уже загруженных массивов на клиенте; при росте мира лучше запрашивать и хранить их по viewport/chunk.
- На экстремально широких экранах или малом zoom возможен компромисс между покрытием и количеством запросов, потому что frontend теперь сознательно уважает backend limit `MaxChunkRadius = 3`.

### Zustand-store

Статус: улучшено, но не завершено.

Побочные эффекты из `addBuilding` убраны, поэтому realtime/sync событие больше не меняет выбранный объект и не закрывает build menu. Store поддерживает positional indexes по id/key, поэтому hot-path select/upsert/delete избегает полного поиска по массиву. Массивы пока сохраняются как публичный API состояния, чтобы не переписывать все consumers за один шаг.

Оставшееся улучшение:

- Нормализовать большие коллекции.
- Ввести selectors для видимой зоны.
- Расширить spatial-index, чтобы `filterVisibleMapObjects` тоже не сканировал весь массив мира.

### Pixi renderer

Статус: существенно улучшено.

Слой монстров отдельный и retained по контейнерам. Terrain/buildings/resources/building overlays теперь тоже retained: `PixiStage` хранит cache по tile/object/overlay keys, повторно использует `Sprite`, `Graphics` и `Container`, а stale children удаляет только при исчезновении из активного набора.

Это закрывает старый full destroy/create path, который мог срабатывать при camera, hover, selection, tiles/buildings/resources и после загрузки textures. Оставшиеся затраты: расчет visible tiles, сортировка, обновление позиций, обновление hit areas и перерисовка `Graphics` fallback/overlay.

Рекомендации:

- Измерить pan/zoom на `?perf=buildings`, `?perf=monsters`, `?perf=mixed` через Chrome Performance.
- Для hit areas можно хранить их рядом с retained object и обновлять при изменении позиции/размера.
- Для fallback Graphics рассмотреть `RenderTexture`/texture atlas.
- Добавить dev-счетчики Pixi children по слоям, чтобы видеть рост/утечки.

### DOM-оверлеи

Файл: `frontend/src/game/IsoMap.tsx`.

DOM-оверлеи используются для строительных таймеров и work badges. Сейчас они рендерятся только для `visibleBuildings`, что хорошо. Но при сотнях видимых производств DOM может начать конкурировать с Pixi и React reconciliation.

Рекомендации:

- Оставить DOM для selected/hover/важных ready-состояний.
- Массовые статусы рисовать в Pixi overlay layer.
- Обновлять таймеры не чаще 1 раза в секунду и только для видимых overlays.

### Ассеты и сборка

Статус: заметно улучшено, но риск все еще средний/высокий.

Факты текущего состояния:

- `npm --prefix frontend run assets:budget`: `210.1 MB` runtime assets across `2035` files.
- `frontend/dist/assets` после production build и `closeBundle` pruning не содержит `.glb`.
- Production build удаляет `.blend`, `.blend1`, `.glb`, backup/review/preview/contact sheets из `dist/assets`.
- Vite во время промежуточной таблицы still lists copied `.glb` before `closeBundle`; фактическая проверка через `find frontend/dist/assets -name '*.glb'` возвращает пустой результат.
- GLB preview остается lazy dev/debug путем: `BuildingModelPreview` лениво грузит `BuildingGlbModel`, а `BuildingGlbModel` лениво грузит `three` и `GLTFLoader`.

Это сильно лучше прежнего runtime бюджета около `726.5 MB`, но `210.1 MB` для веб-игры все еще много. Следующий выигрыш должен прийти от atlas/WebP/AVIF pipeline и выноса source/review материалов из `frontend/public/assets`.

Рекомендации:

- Физически вынести source/review/dev ассеты из `frontend/public/assets` в `tools/assets` или `docs/assets`, чтобы они не участвовали в dev-server public root.
- Сжать GLB через Draco/Meshopt для preview/debug pipeline, но не возвращать GLB в runtime map.
- Для PNG-тайлов и 2D-ассетов собрать texture atlases и рассмотреть WebP/AVIF, где качество приемлемо.
- Уменьшить `ASSET_BUDGET_TOTAL_MB` поэтапно: например 1200 MB -> 600 MB -> 300 MB -> 200 MB -> 150 MB.
- Добавить отчет по top-N runtime files в `assets:budget`, чтобы бюджет был не только gate, но и диагностикой.

### Bundle chunking

Файл: `frontend/vite.config.ts`.

Статус: исправлено для основного route, но требует периодического контроля.

Production build разделяет vendor chunks:

- основной игровой `index`: `220.6 kB`, gzip `55.7 kB`;
- `vendor-react`: `193.8 kB`, gzip `60.5 kB`;
- `vendor-query`: `2.9 kB`, gzip `1.3 kB`;
- `vendor-misc`: `79.6 kB`, gzip `25.1 kB`;
- `vendor-pixi`: `516.8 kB`, gzip `148.8 kB`;
- lazy `vendor-three-preview`: `777.8 kB`, gzip `202.6 kB`.

`vendor-pixi` остается крупным, но он нужен на первом экране карты. `vendor-three-preview` крупнее, но попадает в отдельный lazy chunk для 3D preview/debug, а не в начальную карту. `chunkSizeWarningLimit` поднят до `900`, чтобы Vite не шумел из-за осознанного lazy preview chunk.

Рекомендации:

- Добавить bundle visualizer для периодической диагностики.
- Не дробить Pixi на внутренние ручные chunks без анализа dependency graph: попытка разделить `pixi.js/lib/rendering`, `scene`, `assets`, `core` дает circular chunk warnings.
- Лениво загружать тяжелые панели/debug tools, если они не нужны на первом экране.
- Следить, чтобы `three` не импортировался синхронно из runtime-карты.

## Рекомендуемый План Дальнейших Работ

### Этап 1. Измеримость

1. Добавить Prometheus-style метрики HTTP/DB/simulation/ws.
2. Добавить frontend perf counters для Pixi children, redraw counts, FPS, heap.
3. Добавить backend load seed: 10k buildings, 5k resources, 1k monsters.
4. Прогнать `EXPLAIN ANALYZE` для chunks viewport, buildings viewport, monster tick, spawn count.

### Этап 2. Retained Rendering И Профилирование

1. Зафиксировать baseline FPS/heap/frame time для `?perf=buildings`, `?perf=monsters`, `?perf=mixed`.
2. Добавить счетчики Pixi children/cache created/destroyed per redraw.
3. Разделить redraw hover/selection от redraw terrain/object, если profiling покажет дорогой pan/zoom.
4. Добавить pooling или `RenderTexture` для fallback/overlay graphics, если они станут hot path.

### Этап 3. Нормализация Клиентского Состояния

1. Ввести `byId`/`byKey` структуры в Zustand.
2. Добавить selectors для видимой зоны.
3. Синхронизировать React Query cache и Zustand через общие patch helpers.
4. Снизить число пересчетов `filterVisibleMapObjects` и `occupiedTileKeys`.

### Этап 4. Бэкенд Hot Path

1. Вынести world chunk cache в Redis/edge cache или добавить межпроцессную invalidation, если появится несколько API-инстансов.
2. Добавить `next_tick_at`/claim для MonsterAI при нескольких worker.
3. Оптимизировать placement через footprint queries и транзакцию.
4. Добавить cache в MonsterSpawner relocation.

### Этап 5. Ассеты

1. Вынести source/review ассеты из `public`.
2. Включить compression pipeline для preview GLB и texture assets.
3. Собрать texture atlases для 2D карты.
4. Ужесточить asset budget и добавить top-N отчет.

## Целевые Критерии

Для ближайшей playable alpha:

- Backend p95 для чтения viewport/chunks: до 150 ms на тестовой БД.
- Backend simulation tick: стабильно меньше tick interval, без накопления backlog.
- WebSocket dropped messages: 0 в нормальном сценарии.
- Frontend desktop: 50-60 FPS на обычной карте, не ниже 30 FPS в stress-сценарии.
- Frontend heap после 5 минут pan/zoom/realtime: стабилизируется, не растет монотонно.
- Runtime assets: ближайшая цель меньше 200 MB, далее меньше 150 MB.
- Main app JS chunk: держать меньше 300 KB minified; `three` остается только lazy preview/debug chunk.
- Runtime initial route: загружает только нужный минимум, без скачивания тяжелых ассетов вне экрана.

## Итог

Повторный аудит показывает хороший прогресс: несколько прежних P1-проблем уже закрыты не косметически, а в правильном направлении. Бэкенд теперь меньше рискует упереться в Postgres pool, глобальные выборки монстров и повторное чтение горячих world chunks. Фронтенд перестал делать самые дорогие realtime-инвалидации, уменьшил сетевой churn при drag карты, перевел массовые Pixi-слои на retained cache и убрал GLB из production runtime.

Главные оставшиеся ограничения теперь более конкретные: полноценная нормализация клиентского состояния, spatial-index для видимых объектов, базовая линия tick/backlog под нагрузкой, межпроцессная invalidation для chunk cache, браузерное профилирование retained Pixi path и дальнейшее похудение 2D runtime assets. Систему переписывать не нужно; следующий прирост производительности даст удаление оставшихся full scan участков и подтверждение результатов профилированием.

## Повторный срез 24.10.2026

Замеры сделаны в текущем рабочем дереве, включая незакоммиченные изменения, при `HEAD efdacc4`. Среда: Debian в WSL, AMD Ryzen 5 5500U, Linux/amd64, доступная WSL память 3,5 ГиБ. Значения объема ассетов и сборки относятся к артефактам, а не ко времени загрузки страницы или FPS. Числа из разделов выше сохранены как историческая база.

| Проверка | 14.10.2026 | 24.10.2026 | Вывод |
| --- | ---: | ---: | --- |
| `npm run assets:budget`, runtime public assets | 210,1 MB; 2035 файлов | 498,6 MB; 4246 файлов | Объем вырос на 288,5 MB (около 137%), число файлов — на 2211. Gate проходит, так как его общий предел сейчас 1200 MB; это не подтверждает приемлемую загрузку. |
| Итоговый `frontend/dist/assets` | Не зафиксировано в файле | 499,8 МиБ; 4255 файлов | Объем на диске после production build. Это сумма всех поставляемых ассетов, а не начальный сетевой трафик игрока. |
| PNG в `dist/assets` | Не зафиксировано | 420,3 МиБ; 3649 файлов | Основной вклад в размер дистрибутива. |
| GLB в `dist/assets` | 0 по прошлому аудиту | 57,5 МиБ; 33 файла | Регрессия по составу сборки: `vite.config.ts` сохраняет GLB из `stone_house` и `villa` в `public/assets`. Они поставляются, даже если начальный экран их не скачивает. |
| Основной `index` JS | 220,6 kB; gzip 55,7 kB | 373,5 kB; gzip 89,4 kB | Рост на 152,9 kB без сжатия (около 69%); нужно проверить зависимости и модули основного маршрута. |
| `vendor-pixi` JS | 516,8 kB; gzip 148,8 kB | 516,8 kB; gzip 148,8 kB | Размер практически не изменился. |
| Lazy `vendor-three-preview` JS | 777,8 kB; gzip 202,6 kB | 797,7 kB; gzip 206,8 kB | Чанк остается отдельным, но его размер тоже вырос. |
| Аудиокаталог | Не выделялся в прошлом срезе | 3,0 MB; 310 файлов; preload 6,5 KB | Укладывается в текущие пределы аудио 5 MB и preload 300 KB; не объясняет основной рост ассетов. |

Сборка `NODE_OPTIONS=--max-old-space-size=1024 npm run build` прошла (`tsc -b`, Vite: 2534 модуля, 1 мин 5 с для фазы Vite). После `closeBundle` повторно подсчитаны именно файлы `dist/assets`: промежуточный список Vite до удаления ассетов не использовался как результат. В дистрибутиве также остались каталоги `backup_` (230 файлов, 27,8 МиБ), `preview/` (28 файлов, 4,1 МиБ) и `_test/` (42 файла, 4,3 МиБ). Эти группы могут пересекаться; их объемы нельзя складывать. Текущий фильтр удаляет `.backup-` и отдельные имена с `preview`, но не все пути с каталогами `backup_`, `preview` и `_test`.

`BenchmarkMetricsExposition` выполнен трижды командой `GOCACHE=/tmp/real-city-go-build-cache go test ./internal/adapter/http -run '^$' -bench '^BenchmarkMetricsExposition$' -benchmem -count=3`: 751158, 713892 и 789576 нс/операцию; медиана 751158 нс, примерно 840,9 КБ и 1454 аллокации на операцию. В прежнем локальном срезе было 849103 нс/операцию, 840836 Б и 1454 аллокации. Эти короткие прогоны нельзя считать доказательством ускорения: фоновые процессы и условия запуска не контролировались. Метрика по-прежнему измеряет полный экспорт `/metrics` через `httptest`, включая сбор `runtime.MemStats`, а не стоимость одного игрового запроса.

Проверка `npm test -- --run src/game/dev/performanceScenarios.test.ts src/game/renderer/renderPerformanceMetrics.test.ts` прошла: 2 файла, 3 теста. По коду подтверждено, что `GetOrCreateChunks` по-прежнему создает отсутствующие чанки последовательно, а `IsoMap` фильтрует видимые постройки, ресурсы и монстров из массивов при изменении зависимостей. Это потенциальные ограничения масштабирования, не измеренные в этом срезе как задержка или FPS.

### Приоритет по результатам среза

1. Проверить состав `public/assets` и правила `closeBundle`: убрать из поставки резервные, тестовые и обзорные файлы; отдельно решить, нужны ли 33 GLB в публичном runtime. После этого повторить подсчет бюджета и `dist/assets`.
2. Разобрать рост основного `index` чанка по модулям и проверить, какие функции можно загружать при открытии соответствующего интерфейса. До анализа графа зависимостей нельзя приписать рост одному конкретному компоненту.
3. Провести браузерные `?perf=buildings`, `?perf=monsters`, `?perf=mixed` по существующему протоколу и серверный прогон на реалистичной базе, чтобы получить FPS/frame p95, сетевые p95 и tick/backlog. В этом окружении Chromium не найден, а доступ к Docker API запрещен; браузерных, HTTP/DB и WebSocket чисел в данном срезе нет.

## Оптимизация и проверка 24.10.2026

После предыдущего среза локально установлен Chromium 148 через Playwright. Для браузерного прогона использовались Vite dev-сервер, локальный API с in-memory репозиториями, headless Chromium с программным WebGL (SwiftShader), окно 1440 × 900 CSS px, DPR 1. Каждый сценарий открывался заново; после 10 секунд прогрева снято 8 показаний dev HUD с интервалом 1 секунда. Это один короткий прогон каждого сценария, без pan/zoom; показания HUD используют скользящее окно 1,5 секунды и не являются независимыми повторами. Хосту WSL доступно 3,5 ГиБ памяти и 1 ГиБ swap; во время тяжёлого прогона swap заполнялся. Числа нельзя переносить на реальный desktop GPU или mobile.

Первый браузерный прогон выявил ошибку самого stress-сценария: `Number(null)` превращал отсутствующие `perfBuildings`, `perfMonsters`, `perfResources` и `perfTileRadius` в нули. URL `?perf=buildings` рисовал один тайл и ни одного объекта. Исправлены значения по умолчанию и добавлен тест на 2600 построек, 160 монстров, 260 ресурсов и 4761 тайл. Числа FPS из первого, пустого прогона отброшены.

| Сценарий | До: медиана FPS / медиана frame p95 | После: медиана FPS / медиана frame p95 | Видимые объекты до → после |
| --- | ---: | ---: | --- |
| `?perf=buildings` | 1,4 / 758,6 мс | 2,65 / 767,1 мс | 133 тайла, 468 построек, 94 ресурса, 65 монстров → 133 / 468 / 21 / 47 |
| `?perf=monsters` | 1,1 / 886,0 мс | 1,5 / 804,4 мс | 133 / 283 / 94 / 116 → 133 / 283 / 21 / 56 |
| `?perf=mixed` | 2,25 / 765,0 мс | 1,7 / 721,5 мс | 133 / 468 / 94 / 116 → 133 / 468 / 21 / 56 |

Результаты FPS смешанные: в двух сценариях медиана выше, в `mixed` ниже; с одной попыткой и программным WebGL заявлять доказанное ускорение кадров нельзя. Сокращение числа ресурсов и монстров в кадре является прямым следствием более точных границ видимости для компактных объектов; запас для крупных построек оставлен прежним. Значения frame p95 включают долгие паузы рендера и загрузки текстур. Скриншот подтвердил, что после исправления stress-сценария на карте видны сотни построек, а не пустая сцена.

Исправленные горячие участки:

- `frontend/src/game/renderers/groundRoad.ts` и `renderer/objectLayer/objectDrawData.ts`: индекс соседних дорог/стен создаётся один раз на redraw; раньше каждая видимая дорога повторно просматривала весь массив построек и создавала новый `Set`.
- `frontend/src/game/renderer/PixiStage.tsx`: группы монстров ищутся по `Map`, а графика ресурсных узлов очищается и используется повторно. Счётчик созданных/удалённых Pixi-объектов на последнем redraw в одинаковом сценарии снизился примерно со 102/102 до 11/11 (`buildings`) и с 99/99 до 8/8 (`monsters`).
- `frontend/src/game/renderer/visibleObjects.ts` и `IsoMap.tsx`: для ресурсов и монстров применены границы по фактическому классу размера спрайта вместо общего предела 720 px. Близкие к краю объекты остаются видимыми с запасом.
- `frontend/src/game/state/useGameStore.ts`: секундный `tickConstructions` сохраняет ссылку на массив построек, когда ни одна стройка или грядка не изменилась. Раньше он создавал весь массив заново и повторно отмечал уже готовые грядки каждый тик, что вызывало пересчёт видимых объектов и redraw карты. Индикатор FPS вынесен из состояния `IsoMap` в отдельный компонент.
- `frontend/vite.config.ts` и `frontend/scripts/check-asset-budget.mjs`: из production-сборки исключены каталоги `backup_*`, `preview` и `*_test`, на которые нет ссылок в runtime-коде. Исходные файлы в `public/assets` оставлены на месте. Бюджет runtime-ассетов уменьшился с 498,6 MB / 4246 файлов до 463,6 MB / 3955 файлов; итоговый `dist/assets` — с 499,8 МиБ / 4255 файлов до 464,8 МиБ / 3964 файлов. 33 GLB для существующего 3D-просмотра остаются в поставке.

Локальный API-прогон `python3 scripts/record-observability-baseline.py --base-url http://127.0.0.1:18081 --seconds 10` выполнен до и после клиентских исправлений. Обычный viewport: 47/0 ошибок, p50/p95 9,41/20,92 мс → 48/0 ошибок, 9,21/15,00 мс. Смешанный сценарий: 176/0 ошибок, 20,07/33,84 мс → 176/0 ошибок, 19,22/33,88 мс. Бэкенд не менялся, вторая выборка использовала уже прогретую in-memory карту; эти числа подтверждают отсутствие явной локальной HTTP-регрессии, но не заменяют прежние замеры с Postgres. Docker API в текущем WSL недоступен, поэтому `EXPLAIN ANALYZE`, DB p95 и нагрузка worker здесь не измерялись.

Проверки после исправлений: `npm run lint`, 33 целевых теста для store, stress-сценариев, видимости и рендерных данных, `npm run assets:budget`, production build. Для вывода о реальном FPS всё ещё нужны три повтора на desktop GPU и реальном mobile по [браузерному протоколу](browser-profiling.md), с pan/zoom, trace и одновременно снятыми API/DB/WS метриками. Основной JS-чанк остаётся около 375 kB, а 420 МиБ PNG и 57,5 МиБ GLB в дистрибутиве требуют отдельной ревизии ассетов.

---

# Аудит производительности симуляции монстров и мира

Дата: 01.11.2026. Область: игровая логика и хранилище всех стендов, а не только режим ноутбука. Этот документ фиксирует анализ; оптимизации механики и SQL в рамках аудита не применялись.

## Вывод

На исследованной тестовой базе горячий путь — `MonsterAI.Tick`. В начале наблюдения 7 успешных тиков заняли суммарно 3,379 с; стадия `monster_ai` — 3,065 с, около 91% длительности. При этом каждый активный монстр обрабатывается и записывается практически каждый тик. AI повторно запрашивает постройки и других монстров, выполняет поиск маршрута, создаёт строку события и публикует событие в realtime. Это умножает работу на число живых монстров, даже при пустой карте вокруг них.

Приоритет для всей игры: уменьшить число монстров, требующих полноценного решения на конкретном тике, затем сократить повторные чтения пространства и запись неизменившегося состояния. Снижение частоты общего тика или ограничение CPU контейнера скрывает часть нагрузки и влияет на отзывчивость; его следует рассматривать после изменений алгоритма и замеров.

## Данные и ограничения

В тестовом мире `dev-world` на момент анализа: 104 строки `monsters` (103 `wandering`, 1 `dead`), 44 постройки. Использована существующая тестовая БД с 2 игроками. PostgreSQL в режиме ноутбука имеет `pg_stat_statements`; счётчики после включения расширения показали:

| Операция | Вызовов | Время SQL суммарно | Среднее | Наблюдение |
| --- | ---: | ---: | ---: | --- |
| `UPDATE monsters` | 38 000 | 4 190 мс | 0,110 мс | Один update на обработанного монстра |
| Пространственный `SELECT buildings` | 122 558 | 3 020 мс | 0,025 мс | Около 3,2 запроса на update монстра |
| Пространственный `SELECT monsters` | 44 840 | 2 275 мс | 0,051 мс | Поиск соседнего монстра и другие вызовы |
| `INSERT monster_events` | 38 000 | 1 394 мс | 0,037 мс | Событие на каждый update |
| Выборка активных монстров для тика | 380 | 604 мс | 1,59 мс | До 100 строк в batch |

Снимки получены после запуска стенда и работы симуляции в простое, без игроков в браузере. Время SQL не включает сетевой round-trip, сканирование Go, построение пути, транзакции, логирование и публикацию событий. Числа округлены; счётчики продолжают расти после снимка. Сравнение с нагрузкой реальных игроков и с большой картой ещё требуется. Первые 12 секунд Docker stats ранее дали средние CPU: API 13%, PostgreSQL 26,4%; это отдельное окно и не эквивалентно приведённым суммарным SQL-счётчикам.

`EXPLAIN (ANALYZE, BUFFERS)` на безопасных `SELECT` с картой `dev-world` и типовой областью 20–50 показал последовательный проход 44 построек (0,138 мс) и 103 живых монстров с сортировкой по `updated_at,id` (1,051 мс). Это **не** доказательство плохого плана для большой базы: на малой таблице seq scan может быть дешевле индекса. В тестовой базе накопленный `seq_scan` на `buildings` больше 2,7 млн, но это исторический счётчик, не измерение текущей частоты.

## Как образуется нагрузка

1. `Runner.tick` раз в секунду вызывает `monsters.Tick(..., BatchSize)`; batch по умолчанию 100. `ListActiveForTick` берёт живых монстров по `updated_at,id`, не по сроку следующего действия. Поэтому при 103 живых большинство проходит обработку почти каждый тик. `CatchUp` тоже вызывает весь tick без очереди действий; его частоту под реальными запросами нужно измерить отдельно.
2. Для каждого монстра открывается отдельная транзакция через `UnitOfWork`/`DestructionTransaction`. Внутри `step` ищет ближайшую постройку; `nearestTargetExcept` делает 1–4 пространственных запроса, в зависимости от перехода через край карты. Если цель недостижима, цикл повторяет тот же поиск, исключая одну цель за раз.
3. Если нужна дорога, `nextPassablePath` заново читает постройки в квадрате радиуса 12–28 (также до 4 запросов при wrap) и разворачивает занятые клетки. BFS обходит до 2048 узлов. Кешируются только чанки местности в пределах одного `Tick`, а данные построек и занятости — нет. `isPassable` использует этот кеш, что уже снижает обращения за terrain.
4. При перемещении `applyTraps` читает постройки отдельно для каждой клетки пути. Если цели нет, `collidingMonster` читает соседних монстров. После расчёта выполняется CAS-обновление `monsters`, затем запись `monster_events`. Даже ветка ожидания (`LastMovedAt.After(now)`) возвращает `EventMonsterMoved`, обновляет `UpdatedAt` и проходит эту цепочку. При wandering без изменения координат также возвращается событие движения.
5. После commit `publish` отправляет состояние монстра через EventBus/WebSocket, а `pve.monster.tick` пишет info-лог для каждого обработанного монстра. Клиент применяет события в `features/world/realtime.ts`, кроме того `MonsterSync` периодически получает список (30 с при связи, 8 с без неё). `MonsterService.List` читает **всех** недохлых монстров карты и фильтрует радиус в Go; при росте мира стоимость клиентского опроса растёт с общим числом монстров, а не только с видимой областью.

Индексы уже есть: `idx_monsters_tick (map_id,state,updated_at,id) WHERE state <> 'dead'`, `idx_monsters_map_tile`, `idx_buildings_viewport (map_id,tile_x,tile_y,footprint_w,footprint_h)`. Индекс для footprint помогает лишь части условия: правая граница `tile_x + GREATEST(footprint_w,1) - 1` и аналогичная Y вычисляются в фильтре. На малой таблице planner выбрал seq scan. Дополнительный индекс нельзя назначить без планов на реалистичной большой базе.

## Приоритеты изменений

### P0. Планирование по времени и отсутствие лишних записей

Добавить явное `next_ai_at` либо эквивалентное вычисляемое состояние для живого монстра, выбирать только `next_ai_at <= now`, `ORDER BY next_ai_at,id`, с частичным индексом. Время следующего решения должно учитывать перемещение, атаку, оглушение, истечение срока, а также события изменения цели. Смерть/атака игрока/уничтожение постройки должны пробуждать затронутых монстров или гарантировать небольшой верхний предел задержки. Обязательно проверить starvation при `LIMIT 100`, конкурентных worker и восстановлении после простоя.

Внутри AI отделить «ничего не произошло» от движения. Если координаты, здоровье, цель, состояние и сроки не изменились, не делать `UPDATE`, `monster_events`, публикацию и info-лог. Только повышение `updated_at` для справедливости очереди не должно становиться причиной игрового события; при переходе на `next_ai_at` можно перенести это в планировщик. Для видимого monster movement нужен согласованный протокол, чтобы клиент не терял обновления. Условный CAS и транзакция остаются обязательными при реальном изменении или столкновении.

Ожидаемый эффект: уменьшение числа полных решений, транзакций, SQL-записей, WAL, fanout и client updates. Это гипотеза о величине выигрыша до проверки на базе разного размера.

### P1. Общие пространственные данные в пределах тика

Собрать snapshot построек/их footprint для затронутых чанков один раз за тик; использовать его в выборе цели, поиске пути и проверке ловушек. Альтернатива — пакетная выборка для всех монстров batch, сгруппированных по области. Учитывать wrapped coordinates, много-клеточные постройки, состояние `planned/ruined`, принадлежность созданного монстра и защитные приоритеты. При изменении постройки во время тика snapshot должен инвалидироваться или проверяться повторным чтением/CAS непосредственно перед уроном и расходом ловушки. Кеш нельзя переносить между тиками без механизма инвалидирования.

Для `nearestTargetExcept` сначала фильтровать кандидатов в памяти и повторно использовать результат при исключении недостижимой цели. Для маршрута к текущей цели сохранять путь до препятствия либо пересчитывать только при изменении позиции/препятствия. Замерять отдельно время запроса, построения карты занятости и BFS, а также число попыток на одного монстра. Не менять эвристику выбора цели до проверки поведения защиты и PvP.

Для HTTP-списка монстров заменить полную `ListByMap` на серверную пространственную выборку с 1–4 диапазонами для границ мира; существующий `ListByViewport` — отправная точка. Сохранить точную semantics wrapped distance, лимит запроса и консистентность realtime cache. Это отдельная оптимизация всего сервера при росте мира, не только AI.

### P2. Записи, события и рост таблиц

Оценить объём `monster_events`, WAL и outbox после удаления ложных событий движения. Определить потребителей истории: если каждый тик хранить бессрочно не требуется, ввести документированную retention/архивацию с учётом API, XP, аудита и тестов. Для обычного движения рассмотреть компактные дельты или coalescing событий в пределах чанка/короткого окна, сохранив порядок боя, смерть и факты урона. Измерять `real_city_ws_fanout_total`, drops, размер сообщений и работу браузера при большой популяции.

Сократить per-monster info-логирование: агрегат тика и ошибки оставить, успешный детальный лог сделать debug/сэмплировать. Это снижает сериализацию и запись логов, но нужно проверить требования диагностики и аудита боёв. Сбросить счётчики SQL только в отдельном тестовом прогоне либо сравнивать дельты; не интерпретировать накопленные значения как текущие.

### P3. Индексы и параллелизм по результатам профиля

После P0 проверить план `next_ai_at` на 100, 1 000 и 10 000 монстров. Для пространственного поиска сравнить существующий индекс, expression/generated границы footprint, GiST/SP-GiST или таблицу занятых клеток на реалистичных картах. Оценивать стоимость записи и размер индексов: AI часто обновляет монстров, поэтому дополнительные индексы могут увеличить CPU и WAL. `EXPLAIN (ANALYZE, BUFFERS)` только для безопасных SELECT; изменяющие запросы изучать в транзакции с rollback на копии БД.

Увеличение worker count и размера пула до сокращения запросов может увеличить конкуренцию и блокировки. Проверять только после P0/P1, сохраняя один владелец действия, CAS, атомарность урона и корректный порядок событий. Лимит 5/2 в laptop Compose — локальный бюджет, обычный пул 20/10; архитектурные улучшения должны проверяться с обоими.

## Проверка результата

Снимать одинаковые сценарии: пустой мир, 100/1 000/10 000 монстров, плотные постройки, wrap-граница, барьеры/ловушки, несколько игроков и созданные игроком монстры. Отдельно покой, движение, атака и восстановление после простоя. Сравнивать CPU API/PG, длительность и p95 тика/стадий, `pg_stat_statements` calls/time, WAL/табличный рост, транзакции и ожидание пула, WS fanout, лаг атаки, движение и ошибки CAS. Профиль Go CPU/heap нужен для разделения BFS, работы с построенными объектами, сериализации и логирования; SQL-время само по себе не объясняет все 3,065 с AI.

Критерий приёмки: на той же сцене меньше решений и SQL-операций на живого монстра в секунду, без увеличения задержки боёв и потери событий; на большой карте время HTTP-списка должно зависеть прежде всего от видимых монстров. Фиксировать значения до/после на одной версии данных и конфигурации, затем повторить на общем тестовом стенде и production-подобном размере мира.

## Файлы и замеры

- `backend/internal/worker/simulation/runner.go`, `monster_ai.go` — порядок стадий и AI.
- `backend/internal/adapter/postgres/monster_repo.go`, `building_repo.go`, `uow.go` — SQL и транзакции.
- `backend/internal/service/monster.go` — чтение списка для API.
- `backend/db/migrations/000010_monsters.sql`, `000018_performance_indexes.sql` — схема и индексы.
- `frontend/src/features/monster/MonsterSync.tsx`, `features/world/realtime.ts` — клиентские подписки и polling.
- Замеры текущего сеанса: `/tmp/real-city-profile.dTBsy9`, `/tmp/real-city-resources.nfCXBq`; дополнительные SQL/EXPLAIN получены из работающей тестовой БД 01.11.2026. Пути в `/tmp` не являются постоянным архивом проекта.

## Реализация после аудита: 01.11.2026

Первый пакет изменений внесён в общий код игры. `MonsterService.List` теперь запрашивает только области видимости через `ListByViewport`, учитывая переход через край карты и унаследованные отрицательные координаты монстров. Результаты объединяются по ID и сохраняют прежний порядок. Это устраняет чтение всех монстров мира на каждом HTTP-запросе списка.

В `MonsterAI` повторный поиск цели после исключения недостижимой постройки переиспользует уже прочитанные кандидаты в рамках одного шага монстра. Кеш ограничен транзакцией расчёта одного монстра; между монстрами и тиками он не переносится, чтобы не использовать устаревшее расположение построек. Если игровое состояние не изменилось и событие было бы только фиктивным перемещением, запись в `monster_events` и realtime-публикация пропускаются. Подробный лог каждого обработанного монстра переведён на debug. CAS-обновление строки монстра пока сохраняется для справедливого порядка `updated_at,id`.

Следующий пакет добавил `next_ai_at` для планирования: активный PostgreSQL-репозиторий выбирает только монстров с наступившим сроком, сортирует по `next_ai_at,id`, а CAS-обновление выставляет следующий срок. Блуждающий монстр без цели ждёт 2 секунды, монстр с целью — 1 секунду. Репозиторий памяти использует ту же семантику. Миграция `000052` создаёт поле и индекс, `000053` убирает прежний индекс `idx_monsters_tick` по `updated_at`, чтобы не поддерживать его при каждом обновлении. В тестовой БД обе миграции применены, 2 пользователя сохранились.

На том же тестовом мире (103 живых монстра, без открытой игры) в последующем 12-секундном окне средний CPU API составил 5,4% вместо прежних 13,0%, PostgreSQL — 13,0% вместо 26,4%. Наблюдались тики с 100 обработанными монстрами, чередующиеся с тиками без AI-работы. Это два разных окна времени, поэтому проценты служат ориентиром, а не гарантией для активной игры или большой базы. Целевые Go-тесты AI и списка монстров, а затем полные пакеты `internal/worker/simulation` и `internal/adapter/postgres` прошли. Первоначальные тесты с `LIMIT 1` обновлены, чтобы не зависеть от порядка других стартовых монстров в общем тестовом репозитории. Выявленный полной проверкой откат `next_ai_at` в памяти исправлен: снимок транзакции теперь включает расписание AI, поэтому провал награды XP не задерживает повторную попытку монстра.

Общий пространственный snapshot для всего batch, коалесцирование **реальных** событий и retention истории **пока не выполнены**. Нет механизма немедленного пробуждения AI при появлении постройки или цели: для спокойного монстра задержка обнаружения может достигать 2 секунд. Нужны concurrency-тесты на несколько worker, длительная нагрузка и проверка боя при большом мире. P1/P2 из разделов выше остаются открытыми в указанной части.

---

# Актуальный полный срез: 01.11.2026

Этот раздел заменяет **выводы и оценки**, но сохраняет предыдущие разделы как историю. Замеры выполнены заново на текущем рабочем дереве после описанной выше реализации `next_ai_at`, без очистки существующей базы. Разделены производственный статический фронтенд, dev-сценарии, серверный простой и HTTP-нагрузка. Числа разных окон нельзя складывать или трактовать как сравнение «до/после» на идентичной нагрузке.

## Условия, объём проверки и итоговая оценка

- Стенд: `real-city-test` с `docker-compose.test.yml` и `docker-compose.laptop.yml`; API `127.0.0.1:18080`, статический фронтенд `127.0.0.1:15173`, Vite dev `127.0.0.1:5173` с прокси на API. Хост Ryzen 5 5500U; браузер Chromium headless с ANGLE/Vulkan **SwiftShader** (программный рендер). В Docker четыре контейнера: API, PostgreSQL, Redis и статический фронтенд. Числа CPU в `docker stats` — процент одного ядра, поэтому значения выше 100% допустимы.
- Данные: 104 монстра (103 `wandering`, 1 `dead`), 44 постройки, 3 игрока, 25 чанков в серверном кеше. Третий игрок — тестовый аккаунт, созданный для браузерного входа в ходе этого аудита. База очень мала по числу игровых объектов и **не моделирует** 1000–10 000 монстров, плотную застройку, несколько активных игроков и реальные сетевые задержки.
- Методы: 30 с `measure-laptop-resources.sh` без браузера; отдельные дельты `/metrics` и `pg_stat_statements` за 30 с простоя; два новых HTTP-прогона `record-observability-baseline.py` (10 с и 6 с на каждый сценарий); 18 с Docker stats одновременно со вторым прогоном; `EXPLAIN (ANALYZE, BUFFERS)` только для `SELECT`; свежие `npm run assets:budget` и `NODE_OPTIONS=--max-old-space-size=1024 npm run build`; вход в настоящий браузер и замер Performance API/rAF. Все HTTP-прогоны использовали прогретый мир и локальное соединение.

| Часть | Текущая оценка | Основание и уверенность |
| --- | ---: | --- |
| Бэкенд | **7,0/10** | 0 ошибок в HTTP-прогонах, низкая задержка на маленькой карте, очереди без просрочки и отсутствие ожидания DB pool. Но AI по-прежнему составляет 87,5% времени тиков в простое, выполняет тысячи пространственных чтений за 30 с и непрерывно увеличивает историю; при насыщении viewport API занимает более одного ядра. Уверенность средняя для этого стенда, низкая для большой карты. |
| Фронтенд | **6,5/10, предварительно** | Production-сборка проходит, реальная передача за наблюдаемую сессию гораздо меньше всего каталога. Однако дистрибутив вырос до 972 МБ, программный WebGL показывает тяжёлые кадры, dev-стресс не завершил профилирование, часть графики загрузилась в упрощённом виде. Без desktop GPU и реального mobile оценка FPS не является оценкой игроков. |

**P0:** по полученным данным подтверждённых P0 нет. Нет ошибок HTTP, сбоев тика, потерь WS в простое или просроченных очередей. Это не доказывает отсутствие P0 в production: большой мир, многопользовательский WebSocket и реальное устройство здесь не измерены.

## Фронтенд: свежие замеры

### Сборка, ассеты и первая наблюдаемая сессия

| Показатель | Новый результат 01.11 | Смысл |
| --- | ---: | --- |
| `npm run assets:budget` | 888,0 MB / 6070 runtime-файлов, gate проходит | Проверяет заданный лимит, а не реальную скорость загрузки. 24.10 после прежней оптимизации было 463,6 MB / 3955 файлов: каталог снова значительно вырос. |
| Свежий `dist/assets` | около 972 МиБ / 6214 файлов | Все поставляемые файлы, а не начальный сетевой трафик. |
| GLB в `dist/assets` | 2029 файлов / 548,2 МиБ | Крупнейший новый вклад; 24.10 было 33 GLB / 57,5 МиБ. Проверить, какие уровни/варианты нужны в runtime и какие остаются только исходниками/превью. |
| Главный JS-чанк | 492,02 КБ, gzip 122,58 КБ | 24.10 было около 375 КБ; рост затрагивает входной маршрут. `vendor-pixi` — 516,82 КБ, gzip 148,80 КБ; lazy `vendor-three-preview` — 797,65 КБ, gzip 206,82 КБ. |
| Production build | успешно, фаза Vite 7,37 с | Проверка корректности сборки, не время запуска игры у пользователя. |
| Chromium production, наблюдаемая сессия после входа | 109 resource entries, суммарный `transferSize` 3,15 МиБ; `decodedBodySize` 6,35 МиБ; JS heap 19–26 МиБ | Одно локальное открытие и вход, счётчики накопительные с начала вкладки. Не эквивалентно cold load по сети или всей игровой сессии. `DOMContentLoaded` 505 мс относится к экрану входа. |

Главный чанк и `vendor-pixi` были среди крупнейших переданных файлов (примерно 123 и 151 КБ соответственно). Восьмёрка наиболее крупных индивидуальных запросов также содержит PNG значков ресурсов/оружия по 63–78 КБ. Большой размер `dist` пока не означает скачивание 972 МБ одним игроком, но увеличивает стоимость хранения, деплоя, инвалидации кеша и риск случайного eager-запроса.

### Кадры и доступность графики

На обычной production-карте браузер был доступен для измерения. Один 5-секундный интервал `requestAnimationFrame` при выключенном экономном режиме: **5,3 FPS**, интервал кадра p50/p95 **183,3/316,7 мс**; при включённом режиме: **5,2 FPS**, **200/350 мс**. В UI на момент снимка было 9216 загруженных тайлов. Сравнение двух коротких последовательных окон **не подтверждает** ни ускорение, ни замедление от кнопки: сцена и фоновые загрузки менялись. `requestAnimationFrame` отражает частоту вызовов браузера, не чистое время Pixi. В отдельном снимке GPU-процесс Chromium потреблял более одного ядра, что согласуется с программным WebGL.

Браузер явно сообщил: «Не удалось загрузить часть графики. Карта использует упрощённые объекты». Поэтому эти FPS относятся к **упрощённой** карте в SwiftShader, а не к полной графике на аппаратном GPU. Повторяющийся `403` для `/api/v1/chat/messages?channel=alliance` у игрока вне союза создавал сообщения в консоли каждые ~15 с; это отдельный функциональный/сетевой шум, который нужно убрать из профиля, не выдавая за причину низкого FPS.

Dev-сценарии `?perf=buildings` (значения по умолчанию: 2600/160/260 объектов и 4761 тайл), уменьшенный 300/30/50 с радиусом 16 и минимальный `?perf=mixed&perfBuildings=24&perfMonsters=8&perfResources=6&perfTileRadius=2` были открыты после входа. Playwright не получил стабильный HUD/eval в допустимое время даже на минимальном варианте; скриншот завершился таймаутом 5 с. Следовательно, **новых достоверных чисел HUD FPS, retained caches, pan/zoom и Chrome trace для этих сценариев нет**. Нельзя приписать зависание именно числу построек: оно повторилось и с 24 постройками. Ранее опубликованные в этом файле числа 24.10 остаются историческими, не заменяют текущий замер. Полный протокол 3 × 60 с для desktop/mobile из [browser-profiling.md](browser-profiling.md) в этом окружении не завершён; нужен браузер с аппаратным ускорением и отдельное реальное mobile-устройство.

### Фронтенд: проблемы и приоритеты

| Приоритет | Проблема и доказательство | Последствие и конкретная проверка |
| --- | --- | --- |
| **P1** | Рост runtime-ассетов до 888,0 MB, дистрибутива до 972 МиБ и 2029 GLB. Старый вывод об исключении GLB из production больше не актуален. | Проверить граф зависимостей каждого семейства GLB, исключить исходные/обзорные варианты из поставки и установить отдельные лимиты на GLB, PNG и начальный маршрут. После изменения измерить именно cold/warm network waterfall и кеш. |
| **P1** | В программном Chromium обычная production-карта дала 5,2–5,3 FPS и p95 кадра 317–350 мс; часть графики не загрузилась. Причина этих пауз по trace не установлена. | Повторить на аппаратном desktop GPU и real mobile с полной графикой, 3 прогона покоя/pan/zoom. Снять Chrome Performance, GPU/Memory и dev HUD; разбить время на декодирование текстур, Pixi draw, React commit, GC и сетевые паузы. До этой проверки не переносить FPS SwiftShader на игроков. |
| **P1** | Даже минимальный dev stress не дал ответить HUD/eval/screenshot в headless окружении. | Изолировать dev/HMR, загрузчик ассетов и stress-подмену данных: открыть production обычную карту, затем dev обычную, затем малый stress на том же GPU; фиксировать первый долгий task и ошибки загрузки. Это также блокирует полноценный автоматический регрессионный FPS-базис. |
| **P2** | Главный JS вырос до 492,02 КБ; на первом маршруте загружаются отдельные PNG значков по 63–78 КБ. | Разобрать bundle analyzer и waterfall, перенести тяжёлые панели/превью за явное открытие, уплотнить значки без потери читаемости. Проверить результат по переданным байтам и времени интерактивности. |
| **P2** | `IsoMap.tsx` по-прежнему фильтрует массивы построек, ресурсов и монстров при изменении зависимостей; рядом хранится карта тайлов и ряд polling-запросов (loot 8 с, nearby 5 с, монстры 30/8 с). | На плотной карте измерить React commit и число пересчётов при realtime/pan; затем решить, нужен ли пространственный индекс на клиенте и отмена/разрежение polling при стабильном WS. Текущая маленькая база не доказывает, что этот путь уже узкое место. |
| **P2** | Чат союза у игрока вне союза возвращал `403` с периодом около 15 с. | Не запускать запрос без членства либо корректно обрабатывать запрет без повторного опроса; проверить сокращение лишних запросов/ошибок в консоли. |

## Бэкенд: свежие замеры

### Простой, AI и хранение

В 30-секундном Docker-окне без браузера средний/p95 CPU: API **6,7/15,6%**, PostgreSQL **13,4/31,8%**, Redis **1,0/3,6%**, статический frontend **0,0/0,0%**. Среднее/максимум RAM: API 15,5/17,6 МиБ, PostgreSQL 63,5/64,4 МиБ, Redis 4,1/5,1 МиБ, frontend 7,6/7,6 МиБ. Это текущий простой после планировщика; прежние 5,4/13,0% были другим коротким окном. Средний CPU API+PostgreSQL сейчас около **20% одного ядра** даже без игрока в браузере.

За отдельные 30 с дельты `/metrics`: **30** успешных scheduled ticks, **0** ошибок/паник, суммарная длительность тиков **5,475 с**; стадия `monster_ai` **4,793 с** (87,5%), **1130** обработанных единиц. Стадия построек — 0,062 с; остальные стадии вместе с ней значительно меньше AI. DB pool wait count не вырос. Очереди на снимке: actions 16 pending, **0 due**, outbox/buildings/production без due, dead 0. WS-подключений в простое не было, поэтому нулевые drops не являются тестом fanout.

За то же примерно 30-секундное окно `pg_stat_statements` дало дельты: пространственные чтения `buildings` **3932 вызова / 93,3 мс SQL**, пространственные чтения `monsters` **1770 / 70,1 мс**, `UPDATE monsters` **1230 / 130,5 мс**, `INSERT monster_events` **1230 / 47,1 мс**. Счётчик строк `monster_events` вырос с **1 221 625 до 1 222 855** (1230 записей). Снимки SQL, событий и метрик получены последовательно, поэтому их интервалы отличаются на секунды; нельзя строго делить все числа на одну и ту же длительность. Время SQL не включает round-trip, Go-поиск пути, сериализацию, транзакции и fanout: суммарная длительность AI гораздо больше суммы этих SQL-времён.

Таблица `monster_events` уже содержит около **1,22 млн строк и занимает 630 МБ** с индексами. Текущий прирост в простое около 41 события/с показывает, что устранение ложных событий и планирование сократили, но не устранили постоянное накопление истории. Долговременный темп нельзя экстраполировать по одному окну: движение/бой/число монстров меняются. Нужны политика retention, оценка ценности истории для аудита и контроль размера/WAL.

`EXPLAIN (ANALYZE, BUFFERS)` на этой маленькой базе: выборка due-монстров использовала `Seq Scan` 104 строк и выполнилась за **0,189 мс** (в момент запроса due-строк не было); пространственный `buildings` — `Seq Scan` 44 строк, **0,033 мс**; пространственный `monsters` использовал `idx_monsters_map_tile`, **0,094 мс**. Планировщик обоснованно может выбрать последовательное чтение для 44–104 строк. Эти планы ничего не доказывают о поведении на 10 000 монстров/построек; проверка индекса `next_ai_at` на большой базе остаётся обязательной.

### HTTP, объём ответа и нагрузка

| Новый сценарий локального HTTP | Окно | Запросы / ошибки | RPS | p50 / p95 / max, мс |
| --- | ---: | ---: | ---: | ---: |
| normal viewport, 1 worker | 10 с | 1257 / 0 | 125,69 | 7,53 / 10,62 / 24,60 |
| mixed viewport/chunks, 4 workers | 10 с | 1283 / 0 | 128,13 | 26,93 / 65,40 / 92,89 |
| world seams, 4 workers | 10 с | 2339 / 0 | 232,94 | 12,69 / 43,51 / 62,10 |
| normal viewport, повтор | 6 с | 789 / 0 | 131,35 | 7,31 / 9,82 / 15,73 |
| mixed, повтор | 6 с | 792 / 0 | 131,73 | 26,86 / 64,60 / 84,88 |
| seams, повтор | 6 с | 1415 / 0 | 235,44 | 12,51 / 43,62 / 64,21 |

Итого **7875 запросов, 0 ошибок** в двух прогонах. Во втором прогоне совместный 18-секундный Docker-срез дал средний/p95/max CPU API **135,2/153,5/153,6%**, PostgreSQL **10,9/37,5/38,1%**, Redis около 1%. Нагрузка искусственно насыщает локальный API без пауз игрока и без сети; её нельзя считать реальным RPS. Она показывает, что при повторных viewport-ответах основная CPU-стоимость на этом стенде у API, хотя отдельные SQL-запросы малы. Наблюдаемая длительность `monster_ai` в другом окне, пересекавшемся с первым HTTP-прогоном, составила **22,184 с из 23,728 с** суммарных тиков (21 тик): HTTP-нагрузка конкурирует с симуляцией за CPU, но это не контролируемый A/B-тест.

Отдельный `curl` после прогрева показал размер body: viewport radius 16 — **1 152 443 байта**, radius 48 — **3 205 739 байт**, chunks radius 1 — **1 152 443 байта**. Это локальные несжатые ответы `curl`, не сетевой трафик браузера с компрессией и кешем. При масштабировании игроков и частом обновлении viewport такой объём повышает стоимость JSON-сериализации и сети. `GetOrCreateChunks` уже читает существующие чанки batch-запросом и кеширует их, но отсутствующие создаёт в последовательном цикле; холодная область под конкурентной нагрузкой здесь не замерялась.

### Бэкенд: проблемы и приоритеты

| Приоритет | Проблема и доказательство | Последствие и следующий эксперимент |
| --- | --- | --- |
| **P1** | На 103 живых монстра AI занимает 87,5% времени тиков в простое; 3932 пространственных чтения построек и 1770 чтений монстров за ~30 с. При HTTP-нагрузке суммарное время AI резко растёт. | Общий пространственный snapshot/индекс занятости в пределах тика с проверкой свежести перед уроном, повторное использование маршрута до изменения препятствия, профиль Go CPU/heap для BFS/транзакций/сериализации. Измерить 100/1000/10 000 монстров, ловушки и wrap, p95 тика и задержку атаки; не менять безопасность CAS. |
| **P1** | `monster_events`: ~1,22 млн строк, 630 МБ; +1230 строк за примерно 30 с простоя. | Определить потребителей истории, retention/архив и лимиты таблицы/индексов/WAL. Сохранять боевые и XP-события с требуемой точностью; оценить коалесцирование только обычного перемещения и проверку порядка realtime. |
| **P1** | Под насыщением ~130–235 локальных запросов/с API потребляет в среднем 135,2% ядра; отдельные viewport body 1,15–3,21 МБ. | Профилировать Go CPU именно на mix viewport/chunks, измерить цену JSON, сжатия и генерации тайлов, долю cache hit/miss; затем сравнить дельты чанков/ETag и размер ответов при движении камеры. Повторить с несколькими игроками и реальным WS. |
| **P1** | Нет проверки обратной связи scheduler при появлении цели: спокойный монстр может ждать до 2 с; нет большого стенда для `next_ai_at` и нескольких worker. | На отдельной копии данных проверить 100/1000/10 000 монстров, p95/максимум due-отставания, план индекса, одновременные worker и корректность CAS; при необходимости пробуждать конкретных монстров по изменению мира. |
| **P2** | Холодные `GetOrCreateChunks` всё ещё создаются по одному; текущий HTTP-тест был на прогретой области. | Отдельный параллельный cold-world сценарий с измерением числа INSERT/COPY, p95, конфликтов и lock wait; пакетная/идемпотентная инициализация, если это подтвердится узким местом. |
| **P2** | Отдельные HTTP/DB замеры не включают активный многопользовательский WS; 0 drops при 0 подписок не проверяет fanout. | Снять частоту событий, размер payload, p95 доставки и очереди на тестовых подписчиках без отправки сообщений в общий игровой чат. Проверить reconnection и slow consumers на отдельном тестовом канале/событии. |
| **P2** | `next_ai_at` на 104 строках выбрал `Seq Scan`; пространственный поиск построек на 44 строках также. | Не навязывать индекс по плану маленькой базы. Повторить `EXPLAIN ANALYZE BUFFERS` на масштабированных реалистичных данных, оценить выигрыш чтения против стоимости частых UPDATE и WAL. |

## Порядок дальнейшей проверки и критерии

1. На отдельной воспроизводимой копии мира подготовить 100/1000/10 000 монстров и плотные/пустые застройки; снять CPU/heap-профиль Go, `pg_stat_statements` **дельтами**, tick p50/p95, backlog, WAL и историю за равные 10–30-минутные окна. Цель: меньше операций на одного активного монстра без роста задержки боя и потерь событий.
2. Провести cold/warm viewport с 1/10/50 одновременными игроками, панорамированием и WS-подписками; фиксировать HTTP p95, байты ответа, CPU API/PG, cache hit, DB pool wait и fanout. Цель: отсутствие ошибок и пропущенных событий, управляемые CPU и объём ответов при росте мира.
3. Пересмотреть поставляемые GLB/PNG и граф загрузки; повторить production build, asset budget и cold/warm waterfall. Фиксировать объём начальной сессии отдельно от размера всего дистрибутива.
4. Завершить [браузерный протокол](browser-profiling.md) на desktop с аппаратным GPU и на реальном mobile: все три dev-сценария и обычная карта, 30 с прогрева, 60 с покоя/pan/zoom × 3. Нужны HUD, Performance/Memory trace, число видимых объектов и ошибки графики; до этого не объявлять клиентский FPS-регресс/ускорение доказанным.

Временные артефакты замеров: `/tmp/real-city-resources.LCVBor`, `/tmp/real-city-resources.AJNFDo`, `/tmp/real-city-http-audit.jsonl`, `/tmp/real-city-http-load-audit.jsonl`, `/tmp/real-city-idle-before.prom`, `/tmp/real-city-idle-after.prom`, `/tmp/real-city-sql-before.tsv`, `/tmp/real-city-sql-after.tsv`, `/tmp/real-city-perf-build.log`. Они не входят в репозиторий и могут исчезнуть; числа и условия, необходимые для выводов, приведены выше.

# Дальнейшая проверка пунктов среза 01.11.2026

Дата и окно: 01.11.2026, 08:45–08:48 UTC. Это **дополнительные** измерения на том же работающем тестовом стенде, а не замена полного среза выше. В базе оставались 103 живых монстра, 44 постройки и 25 чанков. Игровые таблицы для масштабного опыта не заполнялись: проверка плана на 100/1000/10 000 монстров проводилась во временной таблице PostgreSQL, которая автоматически удаляется по закрытии сеанса. Рабочее дерево содержит другие незакоммиченные изменения; аудит их не меняет.

## Бэкенд: повторный простой и горячие SQL

В окне 25,1 с по дельтам `/metrics` прошло **25 успешных scheduled ticks**. Они заняли суммарно **4,738 с**, из них `monster_ai` — **4,203 с (88,7%)**, постройки — **0,049 с**, ресурсы — **0,032 с**, остальные этапы и накладные расходы тика вместе — около **0,454 с**. Это согласуется с долей AI 87,5% в предыдущем 30-секундном окне. Одна сумма длительностей не равна загрузке CPU: часть времени тратится на ожидание БД и прочую работу, а метрика суммирует последовательные тики.

За те же 25 с дельты `pg_stat_statements` для четырёх главных SQL: пространственные чтения построек **3231 вызов / 74,5 мс SQL**, пространственные чтения монстров **1477 / 64,4 мс**, `UPDATE monsters` **1027 / 105,5 мс**, `INSERT monster_events` **1027 / 38,2 мс**. Около **3,15 чтения построек** и **1,44 чтения монстров** приходятся на одно обновление монстра в этом окне. Это отношение вызовов, а не точное число запросов одной транзакции: у разных путей AI разное число чтений. Наблюдается устойчивый повтор пространственного поиска, подтверждающий приоритет snapshot/индекса занятости внутри тика. Из этих SQL-времён нельзя вывести долю BFS, Go CPU или сетевого round-trip; для этого по-прежнему нужен профиль процесса.

В отдельном 42,7-секундном окне `monster_events` вырос с **1 269 076 до 1 270 824 строк** (+1748, около 41/с), WAL-позиция PostgreSQL продвинулась на **3 726 736 байт**. Это общий WAL базы, его нельзя целиком приписывать истории монстров. Шесть выборок `docker stats` в этом интервале дали средний CPU API **7,54%**, PostgreSQL **14,72%**, Redis **1,21%**; максимум API/PG **13,38/24,89%**. Память контейнеров API была **17,93–21,65 МиБ**, PostgreSQL **110,3–112,1 МиБ**; показатели зависят от текущих лимитов и кеша, поэтому прямое сравнение RAM с предыдущим окном некорректно. В этот период не проводился HTTP-нагрузочный прогон, **но выполнялся короткий SQL-опыт на временной таблице**; CPU PostgreSQL и общий WAL нельзя называть чистым простоем.

На момент следующего снимка таблица истории достигла **1 274 327 строк и 659 МБ**, из которых около **241 МБ таблица и 418 МБ индексы**. Запрос группировки за последние пять минут обнаружил **11 406 событий `monster.moved` и ни одного другого типа**. Поиск в репозитории обнаружил запись в `monster_repo.go` и realtime-потребителей события, но **не обнаружил чтения `monster_events` из БД**. Это не доказывает, что внешние инструменты не используют таблицу. Перед удалением или ограничением истории нужно проверить внешних потребителей, аудит и требования к восстановлению; затем измерить, сколько места и WAL экономит ограничение хранения *перемещений*, сохранив события боя и XP.

### Проверка индекса планировщика на масштабе

Временная таблица с реальной шириной строки `monsters` (план оценил **193 байта**) и таким же частичным индексом `(map_id, next_ai_at, id) WHERE state <> 'dead'` была заполнена копиями существующих монстров. Примерно 10% строк назначены due; запрос выбирал `SELECT * ... ORDER BY next_ai_at,id LIMIT 100`. После `ANALYZE` получено:

| Размер / due | План | `Execution Time`, локальный кеш |
| --- | --- | ---: |
| 100 / 8 | `Seq Scan` + сортировка | 0,152 мс |
| 1000 / 107 | `Bitmap Index Scan` + сортировка | 1,018 мс |
| 10 000 / 1073 | упорядоченный `Index Scan`, первые 100 строк | 0,648 мс |

Индекс начинает применяться на большей таблице, поэтому прежний `Seq Scan` на 104 монстрах сам по себе не ошибка. Однако эти числа относятся к локально прогретой временной таблице, **не** к полному AI: отсутствуют конкурентные worker, CAS-обновления, изменение индекса, построение маршрутов, реальные распределения `next_ai_at` и задержки диска. Нужен отдельный длительный стенд для p95 due-отставания и стоимости записи при 1000/10 000 активных монстрах.

### Повторный HTTP и фактическое сжатие

Новый прогон `record-observability-baseline.py` по 6 с на сценарий, локальный прогретый API:

| Сценарий | Запросы / ошибки | RPS | p50 / p95 / max, мс |
| --- | ---: | ---: | ---: |
| normal viewport, 1 worker | 760 / 0 | 126,52 | 7,71 / 10,08 / 14,54 |
| mixed viewport/chunks, 4 workers | 722 / 0 | 119,40 | 30,09 / 67,43 / 108,02 |
| world seams, 4 workers | 1338 / 0 | 222,59 | 13,45 / 43,74 / 69,97 |

Итого **2820 запросов без ошибок**. По сравнению с 01.11 p95 близки: normal 9,82→10,08 мс, mixed 64,60→67,43 мс, seams 43,62→43,74 мс. Это разные короткие окна, изменение mixed на 2,83 мс не следует трактовать как регрессию.

Уточнение предыдущей оценки трафика: прямой адрес API `:18080` даже с `Accept-Encoding: gzip, br` отдаёт JSON **без `Content-Encoding`**: viewport radius 16 — **1 152 443 байта**, radius 48 — **3 205 739 байт**. Но игровой фронтенд делает относительные запросы `/api/v1/...` через Caddy на `:15173`, и **на этом фактическом маршруте** Caddy отдал `gzip`: соответственно **52 784** и **147 240 байт**, для chunks radius 1 — **52 784 байта**. Таким образом, утверждение о 1,15–3,21 МБ *передаваемых игроку* на стандартном маршруте было бы неверным. Сервер всё ещё формирует и сериализует полный JSON, а повторные запросы стоят CPU; `Cache-Control` и `ETag` у этих API-ответов не обнаружены. Следующий профиль должен разделить стоимость сериализации API, компрессии прокси и сетевых байтов на реальном маршруте при pan.

Отдельно проверен **warm viewport radius 16 через Caddy** с постоянной отправкой запросов из 1/10/50 параллельных Python-клиентов по 6 с. Это искусственное насыщение одного URL без пауз игрока и WS, а не модель 50 игроков:

| Параллельных клиентов | Ответы / ошибки | RPS | p50 / p95 / max, мс | Сжатие |
| ---: | ---: | ---: | ---: | --- |
| 1 | 210 / 0 | 34,70 | 13,51 / 73,17 / 78,43 | gzip, все ответы |
| 10 | 227 / 0 | 36,56 | 291,92 / 393,93 / 496,86 | gzip, все ответы |
| 50 | 262 / 0 | 36,86 | 1212,84 / 1896,90 / 3490,15 | gzip, все ответы |

Повтор при 10 клиентах и одновременных трёх снимках `docker stats` дал Caddy **34,20 RPS, p95 494,86 мс**, средний CPU Caddy **25,5%**, API **32,1%**, PostgreSQL **16,0%**. В `docker-compose.laptop.yml` Caddy ограничен **0,25 CPU**, поэтому его наблюдаемая загрузка практически упёрлась в квоту. Контрольный прогон того же URL напрямую через API `:18080` при 10 клиентах дал **201,46 RPS, p95 97,59 мс**, CPU API **146,6%**, PostgreSQL **11,1%**; прямой ответ был несжатым (1,15 МБ вместо 52,8 КБ). Различаются и прокси, и компрессия, и переданные байты, поэтому это **не чистый A/B замер только gzip**. Но плато около 35–37 RPS при CPU Caddy у установленной квоты объясняет рост очереди на laptop-стенде. Для него стоит отдельно подобрать квоту/режим компрессии по реальному числу активных игроков и бюджету CPU; переносить этот предел на production-конфигурацию нельзя.

Холодную генерацию чанков с 1/10/50 конкурентными игроками **не запускали**: доступный API использует общий persistent map, а запросы создают в ней новые чанки. Для воспроизводимого теста нужен отдельный map/копия БД и контролируемая очистка кеша; текущий прогон проверяет только warm-путь. WebSocket fanout под подписчиками тоже остаётся непроверенным: при текущем серверном снимке подключений было 0. Искусственные сообщения в общий чат для проверки транспорта не отправлялись.

## Фронтенд: состав поставки и доступность измерений

`npm run assets:budget` повторно прошёл: **888,0 MB / 6070** файлов. Свежий `NODE_OPTIONS=--max-old-space-size=1024 npm run build` прошёл за **7,40 с**. После сборки `dist/assets`: **6214 файлов / 1 005 703 811 байт (959,11 МиБ)**; GLB — **2029 / 548,19 МиБ**, PNG — **3427 / 388,86 МиБ**. Основной JS — **492,02 КБ (gzip 122,58 КБ)**, `vendor-pixi` — **516,82 КБ (gzip 148,80 КБ)**. В этой части роста по сравнению с полным срезом не обнаружено.

Внутри GLB **22 объединённых `*_levels.glb` занимают 143,99 МиБ**; остальные **2007 файлов на уровень/состояние — 404,19 МиБ**. Игровой `buildingRegistry` формирует URL конкретного уровня и состояния; прямых ссылок на объединённые `*_levels.glb` в runtime-коде не найдено, зато они перечислены в generation/manifest/README как исходный объединённый артефакт. Это сильный кандидат на исключение из production-поставки после проверки всех способов открытия моделей. Правила `check-asset-budget.mjs` и `vite.config.ts` расходятся: budget исключает GLB ратуши, а prune-сборка оставляет их; только `buildings/center/town_hall` даёт **135 GLB / 69,77 МиБ**. Поэтому успешный budget-gate **не ограничивает весь фактический `dist`**. Следующий шаг — один общий критерий runtime-файлов для budget и prune, отдельные пределы по GLB/PNG и проверка URL всех игровых моделей.

Статический GLB через Caddy не имеет `Cache-Control`, но отдаёт `ETag` и отвечает **304** на `If-None-Match`: повторная загрузка может быть дешёвой по байтам, но требует проверки у сервера. Размер каталога не равен начальному сетевому трафику. Cold/warm browser waterfall, HUD, FPS, pan/zoom и GPU trace **не получены в этой дополнительной проверке**: локальный Playwright CLI не нашёл Chrome по `/opt/google/chrome/chrome`, а подключённый браузер сообщил о недоступности browser access host. Реального mobile-устройства также нет. Числа FPS 5,2–5,3 из предыдущего среза остаются измерением SwiftShader, не обновлённой оценкой игроков.

## Приоритет на момент дополнительной проверки, до оптимизации фронтенда

- **P0:** подтверждённых новых P0 нет; это относится только к описанным малым локальным нагрузкам.
- **P1, бэкенд:** AI устойчиво занимает около 89% времени тиков; повторные пространственные запросы и записи движения требуют CPU/heap-профиля и безопасного snapshot в пределах тика. История перемещений растёт примерно на 41 строку/с в простое; проверить внешних потребителей и retention/коалесцирование. Проверка планировщика на временных 10 000 строках успешна, но многопоточная симуляция, p95 due-отставания и пробуждение при новой цели не проверены.
- **P1, фронтенд и laptop-прокси:** фактическая поставка содержит 143,99 МиБ объединённых GLB и 69,77 МиБ GLB ратуши вне текущего budget-подсчёта. На laptop-стенде Caddy при квоте 0,25 CPU выходит на плато около 35–37 warm viewport RPS и p95 до 1,90 с при 50 синтетических клиентах; нужно оценить квоту на реальном профиле игры. Нет валидного замера кадров на аппаратном GPU и real mobile; проблему нагрузки рендера нельзя закрыть по этим данным.
- **P2, бэкенд:** API на маршруте игрока сжимается Caddy примерно в 21–22 раза для двух измеренных viewport, поэтому риск *сетевых байтов* ниже прежней предварительной оценки. Остались повторная сериализация, отсутствие HTTP validators, холодные чанки и WebSocket fanout под нагрузкой.
- **P2, фронтенд:** отдельные PNG, рост входного JS, фильтрации в `IsoMap` и polling союза остаются по прошлому анализу; этот прогон не дал новых кадровых доказательств для смены приоритета.

**Оценки сохраняются: фронтенд 6,5/10 (предварительно), бэкенд 7,0/10.** Уточнение gzip снижает оценку сетевого риска, но показало цену компрессии при малой CPU-квоте прокси. План на 10 000 строк подтверждает полезность индекса; эти результаты не закрывают отсутствие реального браузерного профиля и полной нагрузки AI. Артефакты новых локальных окон: `/tmp/real-city-followup-2026-11-01.json`, `/tmp/real-city-followup-metrics-2026-11-01.json`, `/tmp/real-city-followup-caddy-concurrency-2026-11-01.json`; план временной таблицы и HTTP-результаты приведены выше, даже если временные файлы исчезнут.

# Оптимизация фронтенда и повторная оценка 01.11.2026

Этот раздел заменяет **актуальность**, но не исторические результаты предыдущих срезов. Изменения касаются реального игрового маршрута, производственной сборки и режима ноутбука. Бэкенд в этой работе не менялся; его оценка остаётся **7,0/10**. Числа FPS ниже получены в headless Chromium с **SwiftShader**, поэтому не являются оценкой частоты кадров на аппаратном GPU игрока.

## Выполненные изменения

1. `vite.config.ts` и `scripts/check-asset-budget.mjs` используют один критерий runtime-файлов из `scripts/runtime-assets.mjs`. Из поставки удалены 22 объединённых `*_levels.glb`, не используемых игровым URL для конкретного уровня, и исходные PNG ресурсных значков. Модели отдельных уровней, включая ратушу, остаются. Бюджет теперь считает их и проверяет отдельные лимиты всего каталога, GLB, PNG и файла; unit-тест защищает обязательные fallback-спрайты монстров. `.dockerignore` исключает исходные файлы из контекста сборки контейнера.
2. Для 86 ресурсных значков созданы runtime WebP 96 px; компонент значка использует их на игровом маршруте. Исходные PNG сохранены для редактирования. Панели строительства, ресурсов, союза, диагностики ассетов и содержимое вкладки чата загружаются только при открытии. Это уменьшило основной JS-чанк и цену значков при входе.
3. Видимые постройки, ресурсы и монстры выбираются из пространственных индексов по 16-тайловым корзинам, с последней точной проверкой видимости и сохранением исходного порядка. Тайлы для Pixi также предварительно выбираются из индекса. Повторные запросы на полный redraw в одном кадре объединяются через `requestAnimationFrame`; пушечные события в журнале группируются за один проход.
4. При подключённом realtime страховочный опрос loot/nearby идёт раз в 30 с, монстров и ресурсных узлов — раз в 60 с. При потере соединения остаются более короткие интервалы 5–15 с. Чат союза не запрашивается без членства; его вкладка становится недоступной и при потере членства переключается на общий чат. События realtime по-прежнему обновляют данные между опросами.
5. Caddy отдаёт отсутствующие `/assets/*` как `404`, а не HTML игры с кодом `200`; для runtime PNG/WebP/GLB задан `Cache-Control: public, max-age=3600`. В список поставляемых файлов возвращены восемь действительно используемых monster fallback PNG. После этого новая production-сессия открылась без предупреждения о неполной графике. Для laptop-стенда CPU-квота Caddy повышена с 0,25 до 0,5 ядра после отдельного насыщающего теста.

## Повторные измерения

Условия: сборка `NODE_OPTIONS=--max-old-space-size=1024 npm run build`; подсчёт **после** pruning в `frontend/dist/assets`. Сравнение — с дополнительным срезом выше, на той же рабочей копии; изменённые игровые ассеты в рабочем дереве могут влиять на другие сравнения дат.

| Показатель | До | После | Вывод |
| --- | ---: | ---: | --- |
| `dist/assets` | 6214 файлов / 959,11 МиБ | 6205 / **812,21 МиБ** | −146,90 МиБ, примерно −15,3% |
| GLB в `dist/assets` | 2029 / 548,19 МиБ | 2007 / **404,19 МиБ** | −143,99 МиБ; объединённых `*_levels.glb` больше нет |
| PNG в `dist/assets` | 3427 / 388,86 МиБ | 3349 / **385,78 МиБ** | Убраны исходные значки; восемь нужных fallback PNG оставлены |
| Главный JS | 492,02 КБ / gzip 122,58 КБ | **468,78 КБ / gzip 115,83 КБ** | −23,24 КБ исходного JS; `vendor-pixi` остаётся 516,82 КБ / gzip 148,80 КБ |
| 86 исходных значков → runtime | PNG суммарно 4 514 163 байта | WebP суммарно **162 604 байта** | −96,4% для этой группы; браузер загружает только нужные значки |

`npm run assets:budget` проходит: **810,9 MB / 6193** runtime-файла, в том числе **404,2 MB GLB** и **385,8 MB PNG**. Разница с `dist/assets` ожидаема: бюджет считает `public/assets`, а сборка дополнительно содержит JS/CSS и другие выходные файлы. Бюджет теперь учитывает 135 GLB ратуши, которые раньше ошибочно исключались из подсчёта. Текущий каталог остаётся большим: уменьшение *всей поставки* нельзя выдавать за такое же уменьшение сетевого трафика первой сессии.

Микробенчмарк выбора объектов: 10 000 объектов × 200 позиций камеры — линейный проход **472,26 мс**, индекс **61,55 мс**, построение индекса **3,02 мс**; 9216 тайлов × 200 позиций — **110,16 против 29,94 мс**. Тесты подтвердили совпадение видимого набора и порядка, в том числе на шве мира. Это стоимость синтетических функций, **не** измеренное ускорение кадров в браузере.

На производственной карте после исправления fallback-графики три коротких 5-секундных измерения `requestAnimationFrame` в headless Chromium/SwiftShader дали **4,8 / 4,6 / 4,6 FPS**, p50 интервала **200 / 216,6 / 200 мс**, p95 **383,3 / 383,3 / 366,7 мс**. За холодное открытие учтено **107 запросов ресурсов, 626 326 переданных байт, 3 977 292 декодированных байта**; среди них 51 запрос значков, 111 360 переданных байт. Ошибок загрузки ассетов и предупреждения о неполной графике не было. Предыдущие 5,2–5,3 FPS относились к другой сессии с *неполной* графикой; сравнивать эти FPS как A/B-ускорение нельзя.

Dev stress теперь отвечает на HUD/eval. В коротких снимках SwiftShader минимальный сценарий (24 постройки, 8 монстров, 6 ресурсов, radius 2) показал около **6,6 FPS**, p50/p95 **149,3/189 мс**, Pixi children **23/37**, caches **24/24/0/8**, JS heap около **45 МБ**. Сценарий 300/30/50, radius 16 показал около **2,0 FPS**, p50/p95 **483,6/522,8 мс**, children **120/308**, caches **110/248/0/60**, heap около **100 МБ**. После pan из области минимального сценария и возвращения children/caches вернулись к прежним значениям; heap вырос примерно с 49 до 63 МБ без принудительной GC, поэтому вывод об утечке делать нельзя. В профиле CPU dev-сценария 300/30/50 основная доля семплов была idle (3645 из 4954); это не измерение GPU и не объяснение длинных кадров.

В отдельном 35-секундном окне production-карты после первых 5 с загрузки браузер инициировал **59 API-запросов**: inventory 8, attacks 7, production jobs 8, presence 8, profile 4, buildings 4, threats/loot/nearby по 3, chunks/resources/monsters/chat/history по 2 и auth refresh 1. Это включает другие игровые опросы и realtime-инвалидации, поэтому результат нельзя приписывать только четырём изменённым интервалам. Счётчик группировал по пути и не сохранял query string или статус ответа; отсутствие `403` в нём отдельно не доказано. Код и тест проверяют, что без `group_id` запрос канала `alliance` отключён.

Повтор warm viewport через laptop Caddy, gzip, непрерывная синтетическая подача одного URL по 6 с, **после** повышения квоты до 0,5 CPU:

| Клиенты | До: RPS / p95 | После: ответы / ошибки, RPS / p95 |
| ---: | ---: | ---: |
| 1 | 34,70 / 73,17 мс | 438 / 0; **72,96 / 27,57 мс** |
| 10 | 36,56 / 393,93 мс | 500 / 0; **81,26 / 196,99 мс** |
| 50 | 36,86 / 1896,90 мс | 525 / 0; **81,65 / 797,23 мс** |

Это тест предела сжатия и квоты прокси, а не имитация 50 игроков. В кратком снимке после снятия нагрузки Caddy потреблял **0,00% CPU и 96,66 МиБ** контейнерной памяти. При росте квоты верхняя граница CPU под нагрузкой тоже выросла; замер не доказывает уменьшение энергопотребления ноутбука в игровом сеансе.

Проверки: `npm run lint`, **103 тестовых файла / 402 теста**, `npm run assets:budget`, production build, точечные проверки HTTP `404` отсутствующего ассета и `200` SPA-маршрута, загрузка полной карты в production, dev HUD двух stress-сценариев и `git diff --check`. Реальный GPU, мобильное устройство и полный протокол 3 × 60 с из [browser-profiling.md](browser-profiling.md) недоступны в этом окружении.

## Текущая оценка фронтенда и нерешённые вопросы

**Фронтенд: 7,0/10, предварительно.** Размер поставки, входной JS и иконки уменьшились; исправлены ложный `200` для пропавшей графики, опрос союза без членства и масштабирование выбора видимых объектов. Оценка поднята с 6,5, но сдерживается большим каталогом ассетов и отсутствием проверки частоты кадров на настоящем GPU. Исторический список проблем выше отражает состояние **до** этих изменений; его закрытые пункты не входят в актуальный список ниже.

| Приоритет | Актуальный вопрос | Следующий измеримый шаг |
| --- | --- | --- |
| **P0** | Подтверждённых P0 в описанных проверках нет. | Пересмотреть при реальном игровом профиле и ошибках пользователей. |
| **P1** | На SwiftShader даже обычная карта даёт 4,6–4,8 FPS с полной графикой, но программный GPU не позволяет переносить это число на пользователей. В плотном dev stress интервал кадра ещё больше. | Три повтора 60 с покоя, pan и zoom на desktop с аппаратным GPU и реальном mobile, с Chrome Performance/Memory/GPU и HUD; разделить стоимость Pixi draw, декодирования, React, GC и ожидания браузера. Затем оптимизировать подтверждённый горячий путь. |
| **P1** | Runtime-каталог всё ещё 810,9 MB: 404,2 MB GLB и 385,8 MB PNG. Нынешние лимиты защищают от дальнейшего роста, но не задают приемлемый для сети объём всех сценариев. | По частоте использования уровней/состояний провести ревизию моделей и текстур, измерить холодный маршрут и 3D-просмотр, затем применять сжатие/LOD/атласы к реально загружаемым группам с проверкой качества. |
| **P2** | `vendor-pixi` 516,82 КБ, главный JS 468,78 КБ; стартовое открытие передало 626 КБ, но время до интерактивности и сценарий слабого мобильного CPU не измерены. | Снять cold/warm waterfall и Performance trace на целевых устройствах, установить бюджет первого маршрута и при подтверждённом узком месте дробить оставшийся код по действиям игрока. |
| **P2** | Страховочный polling остаётся и при исправном WebSocket (30–60 с); на высокой численности игроков цена зависит от числа открытых клиентов и обновлений. | Замерить запросы/мин и устаревание данных при стабильном соединении и реконнекте с несколькими клиентами; сокращать polling только при подтверждённой надёжности realtime. |

Старые пункты о 22 объединённых GLB, неучтённой ратуше, крупных исходных значках на первом маршруте, `403` чата союза, постоянном полном проходе при каждом выборе видимых объектов и недоступном dev HUD **закрыты** описанными изменениями и проверками. Backend P1/P2 из полного среза остаются актуальными без изменений.
