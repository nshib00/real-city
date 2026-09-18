# API и realtime

## Общий API-клиент

Низкоуровневый клиент находится в `frontend/src/shared/api/client.ts`.

`request<T>(path, init)`:

- добавляет префикс `/api/v1`;
- ставит `Content-Type: application/json`;
- добавляет `Authorization: Bearer <access-token>`, если access token есть;
- для некоторых POST-запросов добавляет `Idempotency-Key`;
- при `401` пробует refresh token и повторяет исходный запрос один раз;
- при ошибке бросает `ApiClientError` с серверным `APIError`.

Idempotency key сейчас добавляется для:

- `POST /buildings`;
- `POST /market/orders`;
- `POST /alliances/invites`.

Токены лежат в `localStorage`:

- `real-city.access-token`;
- `real-city.refresh-token`.

## API-модули

| Модуль | Путь | Ответственность |
| --- | --- | --- |
| Auth API | `frontend/src/features/auth/api.ts` | Регистрация, вход, refresh, logout, профиль игрока |
| Buildings API | `frontend/src/shared/api/buildings.ts` | Каталог, список зданий, постройка, patch-действия, удаление |
| World API | `frontend/src/shared/api/world.ts` | Карта, чанки, viewport, рубка леса |
| Economy API | `frontend/src/shared/api/economy.ts` | Инвентарь, ресурсные узлы, производство, поля |
| Monsters API | `frontend/src/shared/api/monsters.ts` | Монстры, атака, угрозы |
| Social API | `frontend/src/shared/api/social.ts` | Союзы, казна, баффы, чат, рынок |

## Контракты

`frontend/src/shared/contracts/index.ts` реэкспортирует типы из общего пакета `shared/src`:

- `WorldMap`;
- `WorldChunk`;
- `WorldTile`;
- `TerrainType`;
- `Coord`;
- `ObjectKind`;
- `APIError`;
- события мира и другие общие типы.

Так фронтенд не дублирует базовые контракты карты.

## React Query

React Query подключен в `frontend/src/main.tsx` через `QueryClientProvider`. Экземпляр клиента находится в `frontend/src/app/providers/queryClient.ts`.

Основные query keys:

| Query key | Где используется | Что хранит |
| --- | --- | --- |
| `['buildings']` | `BuildingSync`, `BuildMenu`, `Inspector`, realtime | Список зданий |
| `['economy', 'inventory']` | `useInventory`, строительство, производство, сбор | Инвентарь игрока |
| `['world', 'chunks', x, y, radius]` | `useVisibleChunks` | Чанки вокруг центра |
| `['resources', 'nodes']` | `ResourceNodeSync` | Ресурсные узлы |
| `['monsters', x, y, radius]` | `MonsterSync` | Монстры вокруг viewport |
| `['threats', x, y, radius]` | `useThreatLevel` | Угрозы вокруг viewport |
| `['production', 'recipes']` | `ProductionPanel` | Рецепты производства |
| `['production', 'jobs']` | `ProductionPanel` | Производственные задачи |
| `['alliances', 'me']` | `AlliancePanel` | Профиль союза игрока |
| `['market', 'orders']` | `AlliancePanel` | Рыночные ордера |
| `['chat', channel]` | `ChatPanel` | Сообщения чата |

После мутаций компоненты обычно инвалидируют связанные query keys. Например, строительство инвалидирует здания и инвентарь, производство инвалидирует производство и инвентарь, realtime-события карты инвалидируют соответствующие области.

## Синхронизаторы данных

В `App.tsx` подключены компоненты без визуального вывода:

| Компонент | Файл | Что делает |
| --- | --- | --- |
| `BuildingSync` | `frontend/src/features/buildings/BuildingSync.tsx` | Загружает `/buildings`, преобразует ответы в `PlacedBuilding`, кладет в Zustand |
| `ResourceNodeSync` | `frontend/src/features/resources/ResourceNodeSync.tsx` | Загружает `/resources/nodes` каждые 15 секунд |
| `MonsterSync` | `frontend/src/features/monster/MonsterSync.tsx` | Загружает `/monsters` каждые 8 секунд вокруг viewport |
| `WorldRealtime` | `frontend/src/features/world/WorldRealtime.tsx` | Подключает WebSocket и подписку на чанки |
| `ConstructionTicker` | `frontend/src/features/buildings/ConstructionTicker.tsx` | Каждую секунду обновляет локальные таймеры строительства |

## Realtime-клиент

WebSocket-клиент находится в `frontend/src/shared/realtime/client.ts`.

Он:

- строит URL `/api/v1/realtime?token=<access-token>`;
- выбирает `ws:` или `wss:` по текущему протоколу страницы;
- при отсутствии access token пробует refresh token;
- поддерживает статусы `connecting`, `connected`, `reconnecting`, `offline`;
- переподключается с exponential backoff до 15 секунд;
- хранит `lastSeq` и игнорирует старые события;
- умеет подписываться на набор chunk IDs;
- рассылает события подписчикам.

Подписка отправляется сообщением:

```json
{
  "type": "subscribe",
  "chunk_ids": ["dev-world:0:0"],
  "private": true
}
```

## Применение realtime-событий

`frontend/src/features/world/realtime.ts` связывает realtime-клиент, React Query и Zustand.

`useWorldRealtime()`:

- вычисляет текущий центральный чанк через `tileToChunk(viewport.center)`;
- строит список чанков вокруг центра с учетом `viewport.radius`;
- подключает слушатель статуса и событий;
- вызывает `realtimeClient.connect()`;
- обновляет подписку при изменении viewport.

`applyRealtimeEvent()` обрабатывает:

| Тип события | Действие |
| --- | --- |
| `world.tile.changed` | Обновляет tile в store, инвалидирует `['world']` |
| `world.building.placed` | Добавляет/обновляет здание, инвалидирует здания и инвентарь |
| `world.building.updated` | Добавляет/обновляет здание, инвалидирует здания и инвентарь |
| `world.building.removed` | Удаляет здание, инвалидирует здания |
| `world.resource.changed` | Обновляет ресурсный узел, инвалидирует ресурсы |
| `monster.spawned` | Обновляет монстра, инвалидирует монстров |
| `monster.moved` | Обновляет монстра, инвалидирует монстров |
| `monster.attacked` | Обновляет монстра, инвалидирует монстров |
| `monster.damaged` | Обновляет монстра, инвалидирует монстров |
| `monster.died` | Обновляет монстра, инвалидирует монстров |
| `monster.despawned` | Обновляет монстра, инвалидирует монстров |

В обработке монстров поддержаны разные формы payload: поля вида `tile_x`/`tile_y` и Go-подобные поля `Tile.X`/`Tile.Y`, `TargetID`, `MaxHealth`, `UpdatedAt`.

## Поток данных на примере строительства

1. Пользователь выбирает тайл на карте.
2. `IsoMap` кладет выбранный тайл в `useGameStore`.
3. Пользователь открывает `BuildMenu`.
4. `BuildMenu` берет первый уровень построек из `buildCatalog`, проверяет placement и ресурсы.
5. При клике вызывается `placeBuilding({ type, tile_x, tile_y })`.
6. `request()` отправляет `POST /api/v1/buildings` с `Idempotency-Key`.
7. Ответ сервера преобразуется через `toPlacedBuilding`.
8. Здание добавляется в Zustand через `addBuilding`.
9. Инвалидируются `['buildings']` и `['economy', 'inventory']`.
10. Если сервер отправляет realtime-событие `world.building.placed`, оно повторно синхронизирует store.

## Поток данных на примере изменения мира

1. Пользователь кликает на лесной тайл.
2. `IsoMap` проверяет `canChopForestTile`.
3. Если тайл можно рубить, отправляется `chopForest`.
4. При успехе обновляется конкретный `WorldTile` в store.
5. Инвалидируются `['economy', 'inventory']` и `['world']`.
6. Дополнительное realtime-событие `world.tile.changed` также обновит тайл у всех клиентов.
