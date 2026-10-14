# Аудит Производительности И Оптимизации

Дата повторного анализа: 2026-10-14.

Документ обновлен после очередного анализа загрузки ассетов, чанков, realtime-подписок и viewport-запросов. Анализ основан на повторном чтении frontend hot-path карты, React Query cache, Pixi renderer, WebSocket subscriptions, backend world repository и существующих тестах. Полное нагрузочное тестирование, Chrome Performance, WebGL frame capture и `EXPLAIN ANALYZE` для Postgres в рамках этого повторного аудита не запускались, поэтому численные оценки ниже являются инженерной оценкой по архитектуре, коду и тестовой проверке.

## Краткая Оценка

| Часть | Оценка | Состояние |
| --- | ---: | --- |
| Бэкенд | 8.5/10 | Стало заметно лучше: API использует один общий Postgres pool, чанки загружаются batch-запросами, создание tiles переведено на `COPY`, горячие world chunks кэшируются в `WorldRepo` и патчатся при `UpdateTile`, MonsterAI больше не читает всех монстров карты, MonsterSpawner считает живых монстров агрегатом, WebSocket gateway маршрутизирует события через индексы подписок, `/metrics` показывает HTTP/WS-счетчики, а размещение построек больше не читает все здания игрока ради лимита. Главные оставшиеся риски: in-memory rate limit/idempotency, последовательное создание отсутствующих чанков, отсутствие DB/simulation latency metrics, не полностью атомарные игровые действия и отсутствие claim/lock для части simulation flows. |
| Фронтенд | 8.6/10 | Основные прототипные bottleneck-и карты закрыты: realtime-события патчат query-cache, радиус чанков синхронизирован с backend limit `1..3`, world chunks держатся в React Query cache дольше, monster/threat queries и WS subscriptions больше не пересобираются на каждый шаг drag внутри chunk, Zustand хранит индексы для hot-path upsert/select/delete, tile lookup при клике стал `Map`, массовые объекты рисуются через Pixi, terrain/building/resource/overlay слои стали retained по ключам, GLB исключены из production runtime, runtime asset budget держится около `210.1 MB`, а основной app chunk держится около `220.6 kB`. Главные оставшиеся риски: большие коллекции все еще отдаются компонентам массивами, часть DOM-оверлеев может стать узким местом при сотнях производств, Pixi `vendor` chunk остается крупным, нет браузерного профилирования на реальном stress-сценарии. |

Проект уже выглядит достаточно крепко для ранней playable alpha и локального stress-тестирования. До масштабирования на большой общий мир нужно нормализовать клиентское состояние, расширить наблюдаемость до DB/workers и подтвердить гипотезы нагрузочным профилированием на stress-сценариях.

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

Store теперь держит индексы `id/key -> position` для зданий, ресурсных узлов, монстров и world tiles. Это убирает линейный поиск из горячих операций `selectBuilding`, `selectMonster`, `addBuilding`, `upsertResourceNode`, `upsertMonster`, `deleteBuilding`, `setWorldTiles`/`updateWorldTile`. Для частых realtime patch это дешевле прежнего `findIndex` по массиву.

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

Файл: `backend/internal/adapter/http/router.go`.

Статус: базово исправлено для HTTP и WebSocket, но не для DB/workers.

`/metrics` теперь отдает готовность, HTTP request counters/sums по route/method/status class и WebSocket counters/gauges по соединениям, подпискам, fanout и drops. Это уже позволяет видеть рост fan-out и общий HTTP профиль без внешних зависимостей.

Оставшаяся проблема: нет duration/lag метрик на уровне Postgres-запросов, simulation tick, action/outbox queues и production/jobs. Без них все еще трудно отличить медленный SQL от backlog-а worker-а.

Рекомендации:

- DB query duration по hot-path репозиториям: chunks, building placement/viewport, monsters tick, actions, outbox.
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

Главные оставшиеся ограничения теперь более конкретные: полноценная нормализация клиентского состояния, spatial-index для видимых объектов, DB/worker metrics, межпроцессная invalidation для chunk cache, браузерное профилирование retained Pixi path и дальнейшее похудение 2D runtime assets. Систему переписывать не нужно; следующий прирост производительности даст удаление оставшихся full scan участков и подтверждение результатов профилированием.
