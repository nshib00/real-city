# Real City — План реализации

Пунктов плана выполнено: 109/270 (40.4%)

## Подход к логированию

Текущее состояние: репозиторий содержит продуктовые и технические требования, референсы игровых объектов и ассетов, а также базовую прикладную структуру frontend/backend. Логирование частично заложено в backend-каркасе, но игровые события ещё нужно расширять по мере реализации механик. Для multiplayer-стратегии логирование должно покрывать не только HTTP-запросы, но и realtime-события, симуляцию мира, экономику, бои, фоновые задачи, ошибки клиентов и административные действия.

Планируемая модель:

- HTTP middleware: единый access log для каждого запроса (`request_id`, `method`, `path`, route pattern, `status`, `duration_ms`, `player_id`, `ip`, `user_agent`, размер ответа, error class без PII).
- WebSocket gateway: lifecycle соединений (`connected`, `authenticated`, `subscribed`, `disconnected`), latency ping/pong, dropped messages, backpressure, reconnect и ошибки протокола.
- Service layer: бизнес-события (`player.registered`, `building.placed`, `building.completed`, `resource.harvested`, `field.harvested`, `oil_well.claimed`, `fuel.consumed`, `ruin.captured`, `alliance.created`, `combat.resolved`, `monster.moved`, `territory.claimed`, `raid.started`) с идентификаторами сущностей и без секретов.
- Simulation layer: ticks, чанки, очереди действий, deterministic decisions, slow tick warnings, degraded режимы и конфликтующие команды игроков.
- Adapter layer: технические события внешних систем (`postgres`, `redis`, `storage`, `worker`, `websocket`, `asset_pipeline`) — latency, retries, degraded fallback, provider status/error code.
- Domain layer остаётся без логгера и внешних зависимостей.
- Все новые логи должны быть структурированными, с постоянными именами полей и event-name в поле `event`.

## Фаза 0 — Инфраструктурный каркас

| # | Что | Файлы | Статус |
|---|---|---|---|
| 0.1 | Монорепозиторный каркас: `frontend`, `backend`, `shared`, `docs`, единые README и команды разработки | `frontend/`, `backend/`, `shared/`, `README.md`, `Makefile` | ✅ |
| 0.2 | Backend Go module, базовая структура clean/hexagonal architecture, `cmd/api`, `internal/domain`, `internal/service`, `internal/adapter` | `backend/go.mod`, `backend/cmd/api/`, `backend/internal/` | ✅ |
| 0.3 | Frontend Vite + React + TypeScript, strict TS config, базовая структура `app`, `features`, `game`, `shared` | `frontend/package.json`, `frontend/src/`, `frontend/tsconfig.json`, `frontend/vite.config.ts` | ✅ |
| 0.4 | Конфигурация backend: `Config` для server, postgres, redis, JWT/session, websocket, simulation, storage, observability | `backend/pkg/config/config.go`, `backend/.env.example` | ✅ |
| 0.5 | Логгер backend: `slog` JSON в production, text в development, stable fields, helpers для безопасных error attrs | `backend/pkg/logger/` | ✅ |
| 0.6 | Ошибки приложения: типы `NotFound`, `Conflict`, `Forbidden`, `Unauthorized`, `BadRequest`, `Validation`, `RateLimited`; маппинг на HTTP/WS errors | `backend/pkg/apperror/`, `backend/internal/adapter/http/response.go`, `backend/internal/adapter/ws/error.go` | ✅ |
| 0.7 | Подключение к PostgreSQL: pool, ping, migrations bootstrap, graceful close | `backend/internal/adapter/postgres/db.go`, `backend/db/migrations/` | ✅ |
| 0.8 | Подключение к Redis: client, ping, namespaces для cache/session/realtime, graceful close | `backend/internal/adapter/redis/client.go` | ✅ |
| 0.9 | HTTP-ответы и request decoding: `JSON`, `Error`, validation errors, pagination helpers | `backend/internal/adapter/http/` | ✅ |
| 0.10 | `main.go` + `app.go`: DI каркас, lifecycle, graceful shutdown HTTP/WS/workers | `backend/cmd/api/` | ✅ |
| 0.11 | Docker compose для local dev: backend, frontend, postgres, redis, optional storage, healthchecks и volumes | `docker-compose.yml`, `docker-compose.dev.yml` | ✅ |
| 0.12 | Базовый frontend shell: первый экран как игровая поверхность, root layout, providers, error boundary | `frontend/src/app/`, `frontend/src/main.tsx` | ✅ |
| 0.13 | Design tokens и базовые стили: палитра, размеры панелей, typography, z-index слои, CSS reset | `frontend/src/app/styles/`, `frontend/src/shared/ui/` | ✅ |
| 0.14 | Shared contract package: общие enum/types для координат, чанков, объектов, событий, ошибок API | `shared/`, `frontend/src/shared/api/`, `backend/internal/contract/` | ✅ |
| 0.15 | Unit-тесты инфраструктурного каркаса: config, errors, logger helpers, HTTP responses, координатные helpers | `backend/**/*_test.go`, `frontend/src/**/*.test.ts` | ✅ |

---

## Фаза 1 — Аккаунты, игроки и сессии

| # | Что | Файлы | Статус |
|---|---|---|---|
| 1.1 | Domain: `Player`, `Profile`, `Session`, статусы игрока, базовые настройки профиля | `backend/internal/domain/player/` | ✅ |
| 1.2 | Миграции users/players/profiles/sessions с уникальными email/name и timestamps | `backend/db/migrations/` | ✅ |
| 1.3 | SQL-запросы и Postgres-репозитории players/profiles/sessions | `backend/db/query/player.sql`, `backend/internal/adapter/postgres/player_repo.go` | ✅ |
| 1.4 | Хэширование паролей через bcrypt, policy длины и сложности | `backend/internal/domain/player/password.go` | ✅ |
| 1.5 | JWT/session manager: access token, refresh token, rotation, blacklist/revoke | `backend/internal/adapter/jwt/`, `backend/internal/adapter/redis/session_store.go` | ✅ |
| 1.6 | `service/auth`: register, login, refresh, logout, logout all devices | `backend/internal/service/auth.go` | ✅ |
| 1.7 | `service/player`: get/update profile, change password, avatar/settings | `backend/internal/service/player.go` | ✅ |
| 1.8 | DTO auth/player и validation tags | `backend/internal/adapter/http/dto/auth.go`, `backend/internal/adapter/http/dto/player.go` | ✅ |
| 1.9 | Handler auth: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | `backend/internal/adapter/http/handler/auth.go` | ✅ |
| 1.10 | Handler player: `GET /players/me`, `PATCH /players/me`, `PATCH /players/me/password`, `DELETE /players/me` | `backend/internal/adapter/http/handler/player.go` | ✅ |
| 1.11 | Middleware auth/role: userID/playerID в context, admin checks, WS auth reuse | `backend/internal/adapter/http/middleware/auth.go`, `backend/internal/adapter/ws/auth.go` | ✅ |
| 1.12 | Frontend auth flow: login/register screens, token storage strategy, protected app route, logout | `frontend/src/features/auth/`, `frontend/src/shared/api/client.ts` | ✅ |
| 1.13 | Frontend profile panel: имя игрока, avatar placeholder, настройки уведомлений/качества рендера | `frontend/src/features/player/` | ✅ |
| 1.14 | Unit-тесты `service/auth` и session store | `backend/internal/service/tests/auth_test.go`, `backend/internal/adapter/redis/tests/` | ✅ |
| 1.15 | Unit-тесты HTTP auth/player handlers и auth middleware | `backend/internal/adapter/http/handler/tests/`, `backend/internal/adapter/http/middleware/tests/` | ✅ |
| 1.16 | Frontend tests auth store, API client interceptors, protected route | `frontend/src/features/auth/**/*.test.tsx`, `frontend/src/shared/api/**/*.test.ts` | ✅ |
| 1.17 | Событийное логирование auth/player: register/login/logout/refresh, failed auth, profile update, password change; без email/token в логах | `backend/internal/service/auth.go`, `backend/internal/service/player.go` | ✅ |

---

## Фаза 2 — Мировая карта, координаты и чанки

| # | Что | Файлы | Статус |
|---|---|---|---|
| 2.1 | Domain: `WorldMap`, `Chunk`, `Tile`, координаты grid/isometric, terrain types | `backend/internal/domain/world/`, `shared/world/` | ✅ |
| 2.2 | Миграции world_maps/chunks/tiles с индексами по координатам и версии чанка | `backend/db/migrations/` | ✅ |
| 2.3 | SQL-запросы и Postgres-репозитории world/chunk/tile | `backend/db/query/world.sql`, `backend/internal/adapter/postgres/world_repo.go` | ✅ |
| 2.4 | Генератор стартового мира: seed terrain, стартовые зоны, нейтральные ресурсы, безопасные области | `backend/internal/service/worldgen/`, `backend/cmd/seed/` | ✅ |
| 2.5 | `service/world`: get chunk, list visible chunks, claim/load viewport, chunk versioning | `backend/internal/service/world.go` | ✅ |
| 2.6 | HTTP endpoints: `GET /world`, `GET /world/chunks?x=&y=&radius=`, `GET /world/viewport` | `backend/internal/adapter/http/handler/world.go`, `backend/internal/adapter/http/dto/world.go` | ✅ |
| 2.7 | Frontend PixiJS stage: canvas mount, renderer lifecycle, resize, devicePixelRatio, ticker control | `frontend/src/game/renderer/` | ✅ |
| 2.8 | Isometric camera: pan, zoom, bounds, screen↔tile conversion, keyboard/mouse controls | `frontend/src/game/camera/`, `frontend/src/game/coordinates/` | ✅ |
| 2.9 | Terrain renderer: слои terrain/roads/buildings/units/effects/overlays, depth sort по iso координате | `frontend/src/game/layers/`, `frontend/src/game/renderers/terrain.ts` | ✅ |
| 2.10 | Chunk loader на клиенте: TanStack Query cache, prefetch соседних чанков, unload дальних чанков | `frontend/src/features/world/`, `frontend/src/shared/api/world.ts` | ✅ |
| 2.11 | Hover/selection пустого тайла, координаты в inspector, debug overlay для grid/chunk bounds | `frontend/src/features/selection/`, `frontend/src/game/overlays/` | ✅ |
| 2.12 | Unit-тесты координат, chunk math, visibility queries и world service | `backend/internal/domain/world/tests/`, `frontend/src/game/**/*.test.ts` | ✅ |
| 2.13 | Логирование загрузки чанков: viewport requests, cache hit/miss, slow chunk queries, oversized radius | `backend/internal/service/world.go`, `backend/internal/adapter/http/handler/world.go` | ✅ |
| 2.14 | Цикличный мир: toroidal wrap координат по X/Y, нормализация чанков/тайлов, кратчайшие пути через границу карты | `backend/internal/domain/world/wrap.go`, `backend/internal/service/world.go`, `frontend/src/game/coordinates/wrap.ts`, `shared/world/` | ⏳ |
| 2.15 | Укрупнение тайлов примерно в 3 раза: единый `tileSize`, пересчёт iso projection, camera zoom bounds, hit testing и selection | `frontend/src/game/coordinates/iso.ts`, `frontend/src/game/renderer/PixiStage.tsx`, `frontend/src/game/IsoMap.tsx`, `frontend/src/app/styles/index.css` | ✅ |
| 2.16 | Viewport/chunk loading для цикличной карты: корректная загрузка чанков на швах мира и отсутствие дублей при wrap-around | `backend/db/query/world.sql`, `backend/internal/service/world.go`, `frontend/src/features/world/` | ⏳ |
| 2.17 | Уменьшение количества рек и гор примерно в 5 раз по сравнению с текущей генерацией, проверка тестом плотности terrain | `backend/internal/service/worldgen/generator.go`, `backend/internal/service/worldgen/generator_test.go` | ✅ |

---

## Фаза 3 — Игровой HUD и базовый UI

| # | Что | Файлы | Статус |
|---|---|---|---|
| 3.1 | Верхняя панель ресурсов: население/рабочие, монеты, эолийские кристаллы, основные материалы, нефть/бензин и статус защиты | `frontend/src/features/hud/ResourceBar.tsx`, `frontend/src/app/styles/index.css` | ✅ |
| 3.2 | Левая панель инструментов: selection, build, road, repair, attack/raid placeholders; стены создаются через категорию `Оборона` в меню строительства | `frontend/src/features/tools/ToolBar.tsx`, `frontend/src/features/buildings/BuildMenu.tsx` | ✅ |
| 3.3 | Правый inspector: selected tile/object/player, tabs, actions, health/owner/production blocks | `frontend/src/features/inspector/` | ✅ |
| 3.4 | Нижний event log/chat shell: события системы, сообщения игрока, unread indicator | `frontend/src/features/event-log/`, `frontend/src/features/chat/` | ✅ |
| 3.5 | Notification system: toast/feed, severity, batching realtime событий | `frontend/src/features/notifications/` | ✅ |
| 3.6 | Modal/drawer primitives, icon buttons, tooltips, segmented controls, tabs, menus | `frontend/src/shared/ui/` | ✅ |
| 3.7 | Zustand/Jotai stores: tool mode, selection, viewport, UI preferences, realtime status | `frontend/src/shared/store/`, `frontend/src/game/state/` | ✅ |
| 3.8 | Responsive layout: desktop panels, compact mobile/tablet fallback, no text overlap | `frontend/src/app/styles/layout.css`, `frontend/src/features/hud/` | ✅ |
| 3.9 | Empty/loading/error states для карты, API, WS reconnect и authorization | `frontend/src/app/`, `frontend/src/shared/ui/StatusState.tsx` | ✅ |
| 3.10 | Storybook или Ladle для ключевых UI-состояний strategy interface | `frontend/.storybook/` или `frontend/src/stories/` | ✅ |
| 3.11 | Component/unit tests для HUD, toolbar, inspector, stores | `frontend/src/**/*.test.tsx` | ✅ |
| 3.12 | Playwright visual smoke: первый экран, desktop/mobile, карта не пустая, панели не перекрывают критичный контент | `frontend/tests/e2e/ui.spec.ts` | ✅ |
| 3.13 | UI полного списка ресурсов: раскрываемый реестр ресурсов, категории, лимит только для монет, редкие супер-ресурсы, топливо и фильтры | `frontend/src/features/resources/`, `frontend/src/features/hud/ResourceBar.tsx` | ✅ |
| 3.14 | UI союзов: экран Союзного дома, роли, участники, казна, пожертвования, расходы и общие баффы | `frontend/src/features/alliance/` | ✅ |
| 3.15 | Виджет карты: кнопка мини-карты открывает квадрат 5x5 районов как мини-модель мира; клик по ячейке переносит камеру на конкретный тайл выбранного района | `frontend/src/features/minimap/`, `frontend/src/game/state/useGameStore.ts`, `frontend/src/game/coordinates/` | ⏳ |

---

## Фаза 4 — Здания, размещение и строительство

| # | Что | Файлы | Статус |
|---|---|---|---|
| 4.1 | Domain: `Building`, `BuildingType`, `Footprint`, lifecycle states (`planned`, `building`, `active`, `damaged`, `ruined`) | `backend/internal/domain/building/`, `shared/building/` | ✅ |
| 4.2 | Каталог типов зданий MVP: ратуша, землянка, деревянный/каменный дом, многоквартирный дом, вилла, дворец, жилой небоскреб, workshop, warehouse, хранилище монет, market, tower, эволюция стен, road, Союзный дом | `backend/internal/domain/catalog/`, `shared/catalog/buildings.ts` | ✅ |
| 4.3 | Миграции buildings/building_jobs и индексы по owner/chunk/footprint | `backend/db/migrations/` | ✅ |
| 4.4 | SQL-запросы и Postgres-репозитории buildings/build jobs | `backend/db/query/building.sql`, `backend/internal/adapter/postgres/building_repo.go` | ✅ |
| 4.5 | Правила размещения: footprint, занятость тайлов, terrain restrictions, дороги/стены, distance to owned territory | `backend/internal/domain/building/placement.go` | ✅ |
| 4.6 | `service/building`: place, cancel, complete, demolish, repair, list by chunk/player | `backend/internal/service/building.go` | ✅ |
| 4.7 | HTTP endpoints: `POST /buildings`, `GET /buildings/{id}`, `PATCH /buildings/{id}`, `DELETE /buildings/{id}` | `backend/internal/adapter/http/handler/building.go`, `backend/internal/adapter/http/dto/building.go` | ✅ |
| 4.8 | Frontend build catalog: категории, стоимость, время строительства, disabled state при нехватке ресурсов | `frontend/src/features/build-catalog/` | ✅ |
| 4.9 | Placement preview: допустимое/недопустимое размещение, footprint overlay, cost/time preview | `frontend/src/features/build-placement/`, `frontend/src/game/overlays/placement.ts` | ✅ |
| 4.10 | Building renderer: normal/construction/damaged/ruined sprites, anchors, sortOffset, selection outline | `frontend/src/game/renderers/buildings.ts`, `frontend/src/assets/buildings/` | ✅ |
| 4.11 | Server authoritative build flow: клиент отправляет intent, сервер валидирует и возвращает событие изменения чанка | `backend/internal/service/building.go`, `frontend/src/features/build-placement/` | ✅ |
| 4.12 | Unit-тесты placement rules, lifecycle, repository constraints и service errors | `backend/internal/domain/building/tests/`, `backend/internal/service/tests/building_test.go` | ✅ |
| 4.13 | Frontend tests для placement mode, preview states, catalog disabling | `frontend/src/features/build-placement/**/*.test.tsx` | ✅ |
| 4.14 | Событийное логирование строительства: place/cancel/complete/demolish/repair, invalid placement, resource shortage; поля `building_id`, `building_type`, `tile`, `player_id`, `chunk_id` | `backend/internal/service/building.go` | ✅ |
| 4.15 | Правила времени строительства и апгрейдов: материалы, монеты, свободное население, занятость строителей, остановка/повреждение стройки | `backend/internal/domain/building/build_rules.go`, `backend/internal/service/building.go`, `shared/catalog/buildings.ts` | ✅ |
| 4.16 | Лимит построек от ратуши: дороги не расходуют лимит, все остальные постройки расходуют; апгрейд ратуши повышает лимит | `backend/internal/domain/building/limits.go`, `backend/internal/domain/catalog/buildings.go`, `frontend/src/features/build-catalog/` | ✅ |
| 4.17 | Жилая ветка: Землянка → деревянный дом → каменный дом → ветки `многоквартирный дом/жилой небоскреб` и `вилла/дворец` | `backend/internal/domain/catalog/housing.go`, `shared/catalog/buildings.ts`, `frontend/src/assets/buildings/housing/` | ✅ |

---

## Фаза 5 — Экономика, ресурсы и инвентарь

| # | Что | Файлы | Статус |
|---|---|---|---|
| 5.1 | Domain: `ResourceType`, `Inventory`, `ProductionRecipe`, `ResourceNode`, `StorageLimit` | `backend/internal/domain/economy/` | ✅ |
| 5.2 | Миграции player_inventories/resource_nodes/production_jobs/transactions | `backend/db/migrations/` | ✅ |
| 5.3 | SQL-запросы и репозитории inventory/resources/production | `backend/db/query/economy.sql`, `backend/internal/adapter/postgres/economy_repo.go` | ✅ |
| 5.4 | Каталог ресурсов и production recipes для MVP: монеты, эолийские кристаллы, большой список материалов, нефть, бензин, супер-ресурсы, добыча, переработка, хранение, потребление рабочих | `backend/internal/domain/catalog/economy.go`, `shared/catalog/resources.ts` | ✅ |
| 5.5 | `service/economy`: get inventory, reserve/spend/add resources, calculate coin capacity from хранилища монет, transaction ledger; остальные ресурсы без лимитов | `backend/internal/service/economy.go` | ✅ |
| 5.6 | `service/resource`: spawn/list/claim/harvest resource nodes, depletion/respawn | `backend/internal/service/resource.go` | ✅ |
| 5.7 | Production ticks: запуск/завершение производства, offline progress, idempotent completion | `backend/internal/service/production.go`, `backend/internal/worker/production_worker.go` | ✅ |
| 5.8 | HTTP endpoints: inventory, resource node details, harvest/start production/cancel production | `backend/internal/adapter/http/handler/economy.go`, `backend/internal/adapter/http/dto/economy.go` | ✅ |
| 5.9 | Frontend resource bar wiring: live values, coin capacity warnings, spend animations, insufficient resources feedback; остальные ресурсы без лимитов | `frontend/src/features/hud/`, `frontend/src/features/economy/` | ✅ |
| 5.10 | Resource node renderer and inspector: neutral/claimed/depleted, owner, time to respawn | `frontend/src/game/renderers/resources.ts`, `frontend/src/features/inspector/` | ✅ |
| 5.11 | Production UI: building recipes, timers, queue status, collect/complete feedback | `frontend/src/features/production/` | ✅ |
| 5.12 | Unit-тесты economy domain/service: spend/add, лимит монет, отсутствие лимитов у материалов, recipes, production timers, harvest rules | `backend/internal/domain/economy/tests/`, `backend/internal/service/tests/economy_test.go` | ✅ |
| 5.13 | Frontend tests для resource bar, production panel, insufficient resources states | `frontend/src/features/economy/**/*.test.tsx`, `frontend/src/features/production/**/*.test.tsx` | ✅ |
| 5.14 | Событийное логирование экономики: resource spent/added/harvested, production started/completed, coin capacity overflow | `backend/internal/service/economy.go`, `backend/internal/service/production.go` | ✅ |
| 5.15 | Нефтяные скважины: spawn/claim/harvest нефти, лимиты скважин, спорные состояния, интеграция с территорией и складами | `backend/internal/domain/economy/oil.go`, `backend/internal/service/resource.go`, `frontend/src/game/renderers/resources.ts` | ✅ |
| 5.16 | Нефтеперерабатывающий завод и бензин: рецепт `нефть -> бензин`, хранение топлива, потребление бензина заводами средних/поздних уровней | `backend/internal/domain/catalog/production.go`, `backend/internal/service/production.go`, `shared/catalog/resources.ts` | ✅ |
| 5.17 | Поля/грядки: стадии роста, сбор ресурсов и монет, шанс супер-версии 0.5-1%, супер-продукты и отдельные награды | `backend/internal/domain/economy/field.go`, `backend/internal/service/field.go`, `frontend/src/features/fields/` | ✅ |
| 5.18 | Население как рабочая сила экономики: назначение на стройку, поля, заводы, защиту, ремонт; свободные/занятые жители | `backend/internal/domain/player/population.go`, `backend/internal/service/population.go`, `frontend/src/features/population/` | ✅ |

---

## Фаза 6 — Realtime WebSocket и события мира

| # | Что | Файлы | Статус |
|---|---|---|---|
| 6.1 | WebSocket gateway: upgrade, auth, connection registry, player presence, graceful close | `backend/internal/adapter/ws/gateway.go` | ✅ |
| 6.2 | Protocol envelope: `type`, `event_id`, `seq`, `sent_at`, `chunk_id`, payload versioning | `backend/internal/adapter/ws/protocol.go`, `shared/events/` | ✅ |
| 6.3 | Subscription model: viewport/chunk subscriptions, player private channel, alliance channel placeholders | `backend/internal/adapter/ws/subscription.go` | ✅ |
| 6.4 | Event bus внутри backend: publish/subscribe для domain events без привязки к WS | `backend/internal/service/eventbus.go` | ✅ |
| 6.5 | Delta events для карты: tile changed, building placed/updated/removed, resources changed, combat event, monster event | `shared/events/world.ts`, `backend/internal/service/events.go` | ✅ |
| 6.6 | Backpressure и rate limits: bounded send queue, disconnect slow clients, command throttling | `backend/internal/adapter/ws/connection.go`, `backend/internal/adapter/ws/ratelimit.go` | ✅ |
| 6.7 | Client WS manager: reconnect, auth refresh, subscriptions by viewport, event ordering, missed-event recovery | `frontend/src/shared/realtime/`, `frontend/src/features/world/realtime.ts` | ✅ |
| 6.8 | Optimistic UI policy: только безопасные previews; authoritative server events update canonical state | `frontend/src/game/state/`, `frontend/src/features/build-placement/` | ✅ |
| 6.9 | Presence indicators: online/offline state, player cursor/selection optional для dev | `backend/internal/service/presence.go`, `frontend/src/features/presence/` | ✅ |
| 6.10 | Unit-тесты WS protocol, subscriptions, auth, backpressure, event fanout | `backend/internal/adapter/ws/tests/` | ✅ |
| 6.11 | Frontend tests WS reconnect/subscription/update reducers | `frontend/src/shared/realtime/**/*.test.ts`, `frontend/src/features/world/**/*.test.ts` | ✅ |
| 6.12 | Логирование realtime: connect/disconnect/auth fail/subscribe/unsubscribe/dropped message/reconnect hints | `backend/internal/adapter/ws/`, `frontend/src/shared/realtime/` | ✅ |

---

## Фаза 7 — Симуляция мира, таймеры и фоновые задачи

Целевой подход: авторитетная серверная симуляция с явными тиками, очередями действий и идемпотентными обработчиками. Redis используется для временных очередей и distributed locks, PostgreSQL остаётся источником истины. Фоновые задачи не должны менять состояние мира без транзакционной фиксации в БД и публикации событий для клиентов.

В эту фазу входят только базовые процессы MVP: завершение строительства, производство ресурсов, respawn ресурсных узлов, перемещение простых монстров, decay/repair timers и доставка realtime-событий. Глубокие рейды, рынки и союзные войны планируются позднее.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 7.1 | Simulation config: tick interval, batch size, worker concurrency, lock TTL, catch-up limit, shutdown timeout | `backend/pkg/config/config.go`, `backend/.env.example` | ⏳ |
| 7.2 | Domain action queue: `GameAction`, statuses, due_at, idempotency key, actor/target refs | `backend/internal/domain/action/`, `backend/db/migrations/` | ⏳ |
| 7.3 | PostgreSQL action repository: append/fetch due with lock/skip locked/mark done/mark failed/retry | `backend/db/query/action.sql`, `backend/internal/adapter/postgres/action_repo.go` | ⏳ |
| 7.4 | Transaction boundary для симуляции: unit of work, atomic state update + event append | `backend/internal/service/ports.go`, `backend/internal/adapter/postgres/uow.go` | ⏳ |
| 7.5 | Simulation worker lifecycle: start/stop, leader lock, tick metrics, panic recovery | `backend/internal/worker/simulation/`, `backend/cmd/worker/` | ⏳ |
| 7.6 | Завершение строительства по таймеру: activate building, update chunk version, publish event | `backend/internal/worker/simulation/building.go` | ⏳ |
| 7.7 | Production tick: calculate finished production jobs, add resources with capacity handling, publish deltas | `backend/internal/worker/simulation/production.go` | ⏳ |
| 7.8 | Resource respawn/depletion tick: restore nodes, spawn limited neutral nodes around active areas | `backend/internal/worker/simulation/resources.go` | ⏳ |
| 7.9 | Basic offline progress: bounded catch-up при login/load player state | `backend/internal/service/economy.go`, `backend/internal/service/player.go` | ⏳ |
| 7.10 | Outbox events для надёжной доставки realtime/email/future notifications | `backend/db/migrations/`, `backend/internal/domain/event/`, `backend/internal/adapter/postgres/outbox_repo.go` | ⏳ |
| 7.11 | Dispatcher outbox → WS/event bus: retry, dead-letter, idempotent event ids | `backend/internal/worker/outbox_dispatcher.go` | ⏳ |
| 7.12 | Unit-тесты simulation ticks, locking, idempotency, retries и event publication | `backend/internal/worker/simulation/**/*_test.go`, `backend/internal/service/tests/action_test.go` | ⏳ |
| 7.13 | Логирование simulation/outbox: tick start/success/failure, slow tick, action result, retry/dead-letter | `backend/internal/worker/`, `backend/internal/service/` | ⏳ |
| 7.14 | Tick полей и грядок: рост по стадиям, готовность урожая, супер-версия, начисление ресурсов и монет | `backend/internal/worker/simulation/fields.go`, `backend/internal/service/field.go` | ⏳ |
| 7.15 | Tick топлива: потребление бензина активными заводами, остановка/замедление при нехватке, offline catch-up | `backend/internal/worker/simulation/production.go`, `backend/internal/domain/economy/fuel.go` | ⏳ |
| 7.16 | Tick нефтяных скважин: добыча нефти, contested ownership, depletion/respawn или rate limiting добычи | `backend/internal/worker/simulation/oil.go`, `backend/internal/service/resource.go` | ⏳ |

---

## Фаза 8 — Монстры, PvE и угрозы

| # | Что | Файлы | Статус |
|---|---|---|---|
| 8.1 | Domain: `Monster`, `MonsterType`, `Threat`, `MovementIntent`, базовые AI states | `backend/internal/domain/monster/` | ⏳ |
| 8.2 | Миграции monsters/monster_spawn_points/monster_events | `backend/db/migrations/` | ⏳ |
| 8.3 | SQL-запросы и репозитории monsters/spawns | `backend/db/query/monster.sql`, `backend/internal/adapter/postgres/monster_repo.go` | ⏳ |
| 8.4 | Каталог монстров MVP: roaming melee, resource guardian, ruins guardian с параметрами hp/damage/speed/aggro | `backend/internal/domain/catalog/monsters.go`, `shared/catalog/monsters.ts` | ⏳ |
| 8.5 | AI movement tick: wandering, aggro radius, path constraints, chunk transitions | `backend/internal/worker/simulation/monster_ai.go` | ⏳ |
| 8.6 | PvE combat rules: attack building/player unit placeholder, damage, death, loot/reward, cooldown | `backend/internal/domain/combat/`, `backend/internal/service/combat.go` | ⏳ |
| 8.7 | Threat service: calculate danger around player territory, notify clients, inspector status | `backend/internal/service/threat.go` | ⏳ |
| 8.8 | HTTP endpoints: list monsters in viewport, monster details, attack/defend action | `backend/internal/adapter/http/handler/monster.go`, `backend/internal/adapter/http/dto/monster.go` | ⏳ |
| 8.9 | Frontend monster renderer: sprite states, health bars, aggro/target overlay, movement interpolation | `frontend/src/game/renderers/monsters.ts`, `frontend/src/features/monster/` | ⏳ |
| 8.10 | Inspector states для выбранного монстра и угрозы рядом с постройками | `frontend/src/features/inspector/MonsterInspector.tsx`, `frontend/src/features/threat/` | ⏳ |
| 8.11 | Realtime monster events: moved/attacked/damaged/died/spawned/despawned | `shared/events/monster.ts`, `frontend/src/features/monster/realtime.ts` | ⏳ |
| 8.12 | Unit-тесты AI movement, aggro, combat calculations, loot, threat service | `backend/internal/domain/monster/tests/`, `backend/internal/domain/combat/tests/` | ⏳ |
| 8.13 | Frontend tests monster rendering state reducers and inspector actions | `frontend/src/features/monster/**/*.test.tsx` | ⏳ |
| 8.14 | Событийное логирование PvE: spawn/move/aggro/attack/damage/death/reward; поля `monster_id`, `monster_type`, `target_id`, `chunk_id` | `backend/internal/service/combat.go`, `backend/internal/worker/simulation/monster_ai.go` | ⏳ |

---

## Фаза 9 — Территория, владение и защита

| # | Что | Файлы | Статус |
|---|---|---|---|
| 9.1 | Domain: `Territory`, `Claim`, `ProtectionZone`, `Border`, `Influence` | `backend/internal/domain/territory/` | ⏳ |
| 9.2 | Миграции territory_claims/protection_zones/border_events | `backend/db/migrations/` | ⏳ |
| 9.3 | SQL-запросы и репозитории territory/protection | `backend/db/query/territory.sql`, `backend/internal/adapter/postgres/territory_repo.go` | ⏳ |
| 9.4 | Правила влияния построек: city center, roads, towers, walls, contested zones | `backend/internal/domain/territory/rules.go` | ⏳ |
| 9.5 | `service/territory`: recalculate claims, get owner/protection for tile, validate expansion | `backend/internal/service/territory.go` | ⏳ |
| 9.6 | Интеграция placement rules с территорией: запрет/стоимость/риск строительства вне влияния | `backend/internal/domain/building/placement.go`, `backend/internal/service/building.go` | ⏳ |
| 9.7 | Defense service: tower coverage, wall blocking, protected/offline status, vulnerability windows | `backend/internal/service/defense.go`, `backend/internal/domain/combat/defense.go` | ⏳ |
| 9.8 | HTTP endpoints: territory by viewport, tile ownership/protection, player borders | `backend/internal/adapter/http/handler/territory.go`, `backend/internal/adapter/http/dto/territory.go` | ⏳ |
| 9.9 | Frontend territory overlay: owner colors, contested/protected/danger states, opacity controls | `frontend/src/game/overlays/territory.ts`, `frontend/src/features/territory/` | ⏳ |
| 9.10 | Inspector ownership blocks: owner, protection, contest status, allowed actions | `frontend/src/features/inspector/` | ⏳ |
| 9.11 | Realtime territory events: claimed/lost/contested/protection changed | `shared/events/territory.ts`, `frontend/src/features/territory/realtime.ts` | ⏳ |
| 9.12 | Unit-тесты territory rules, protection calculations, placement integration | `backend/internal/domain/territory/tests/`, `backend/internal/service/tests/territory_test.go` | ⏳ |
| 9.13 | Событийное логирование территории: claim/recalculate/protection changed/contested, invalid expansion | `backend/internal/service/territory.go`, `backend/internal/service/defense.go` | ⏳ |

---

## Фаза 10 — PvP, рейды, разрушения и ремонт

| # | Что | Файлы | Статус |
|---|---|---|---|
| 10.1 | Domain combat расширение: `Raid`, `AttackIntent`, `DamageEvent`, `LootTable`, `Cooldown` | `backend/internal/domain/combat/` | ⏳ |
| 10.2 | Миграции raids/combat_events/cooldowns/repair_jobs | `backend/db/migrations/` | ⏳ |
| 10.3 | SQL-запросы и репозитории raids/combat/cooldowns | `backend/db/query/combat.sql`, `backend/internal/adapter/postgres/combat_repo.go` | ⏳ |
| 10.4 | Rules: валидность цели, distance/travel time, protection windows, damage, loot limits, anti-grief caps | `backend/internal/domain/combat/rules.go` | ⏳ |
| 10.5 | `service/raid`: start/cancel/resolve raid, schedule travel, apply damage/loot, publish events | `backend/internal/service/raid.go` | ⏳ |
| 10.6 | `service/repair`: start/complete repair, resource cost, restore from damaged/ruined state where allowed | `backend/internal/service/repair.go` | ⏳ |
| 10.7 | HTTP endpoints: start raid, raid details/list, cancel raid, repair building | `backend/internal/adapter/http/handler/raid.go`, `backend/internal/adapter/http/handler/repair.go` | ⏳ |
| 10.8 | Frontend attack/raid tool mode: target validation overlay, travel/cost preview, confirmation dialog | `frontend/src/features/raid/`, `frontend/src/features/tools/` | ⏳ |
| 10.9 | Combat event renderer: damage numbers, attack lines, building damaged/ruined visual states | `frontend/src/game/effects/combat.ts`, `frontend/src/game/renderers/buildings.ts` | ⏳ |
| 10.10 | Raid inspector/event log: incoming/outgoing raids, cooldowns, results, loot summary | `frontend/src/features/raid/RaidPanel.tsx`, `frontend/src/features/event-log/` | ⏳ |
| 10.11 | Anti-abuse safeguards: rate limits, cooldown checks, offline protection policy, max losses per window | `backend/internal/service/raid.go`, `backend/internal/adapter/http/middleware/ratelimit.go` | ⏳ |
| 10.12 | Unit-тесты combat/raid/repair rules, edge cases, anti-grief constraints | `backend/internal/domain/combat/tests/`, `backend/internal/service/tests/raid_test.go` | ⏳ |
| 10.13 | Frontend tests raid mode, invalid targets, incoming raid notifications | `frontend/src/features/raid/**/*.test.tsx` | ⏳ |
| 10.14 | Событийное логирование PvP: raid start/resolve/cancel, damage/loot/repair, forbidden target, cooldown denial | `backend/internal/service/raid.go`, `backend/internal/service/repair.go` | ⏳ |

---

## Фаза 11 — Союзы, чат, рынок и социальные механики

| # | Что | Файлы | Статус |
|---|---|---|---|
| 11.1 | Domain alliances: `Alliance`, `AllianceMembership`, роли `leader/deputy/officer/member`, назначение казначея одному заместителю, invites, permissions | `backend/internal/domain/alliance/` | ⏳ |
| 11.2 | Миграции alliances/alliance_members/alliance_invites/alliance_treasury/alliance_buffs/chat_messages/market_orders | `backend/db/migrations/` | ⏳ |
| 11.3 | SQL-запросы и репозитории alliances/treasury/buffs/chat/market | `backend/db/query/alliance.sql`, `backend/db/query/chat.sql`, `backend/db/query/market.sql` | ⏳ |
| 11.4 | `service/alliance`: create via Союзный дом, invite, accept/decline, roles, deputy limit 2, treasurer assignment, leave/kick, profile | `backend/internal/service/alliance.go` | ⏳ |
| 11.5 | Alliance territory placeholders: союзное владение/помощь для руин, нефтяных скважин и защиты без full alliance warfare | `backend/internal/service/territory.go`, `backend/internal/domain/alliance/` | ⏳ |
| 11.6 | Chat service: global/nearby/alliance/private channels, moderation flags, pagination | `backend/internal/service/chat.go` | ⏳ |
| 11.7 | Market service MVP: create buy/sell order, cancel, match simple resource trades, fees | `backend/internal/service/market.go`, `backend/internal/domain/market/` | ⏳ |
| 11.8 | HTTP endpoints alliances/chat/market | `backend/internal/adapter/http/handler/alliance.go`, `backend/internal/adapter/http/handler/chat.go`, `backend/internal/adapter/http/handler/market.go` | ⏳ |
| 11.9 | Realtime chat and alliance events | `shared/events/chat.ts`, `shared/events/alliance.ts`, `frontend/src/features/chat/realtime.ts` | ⏳ |
| 11.10 | Frontend alliance panel: membership, invites, roles, treasurer, Союзный дом, казна, баффы, статус союза | `frontend/src/features/alliance/` | ⏳ |
| 11.11 | Frontend chat UI: channels, unread, moderation-safe rendering, reconnect handling | `frontend/src/features/chat/` | ⏳ |
| 11.12 | Frontend market UI: orders list, create/cancel, inventory impact preview | `frontend/src/features/market/` | ⏳ |
| 11.13 | Unit-тесты alliance/chat/market services and permissions | `backend/internal/service/tests/alliance_test.go`, `backend/internal/service/tests/chat_test.go`, `backend/internal/service/tests/market_test.go` | ⏳ |
| 11.14 | Событийное логирование social: alliance create/invite/role/treasury/buff, chat moderation events, market order lifecycle | `backend/internal/service/alliance.go`, `backend/internal/service/chat.go`, `backend/internal/service/market.go` | ⏳ |
| 11.15 | Союзный дом как постройка: уровни, лимит участников, открытие офицеров/казначея/баффов, синхронизация с каталогом зданий | `backend/internal/domain/catalog/alliance_buildings.go`, `backend/internal/service/alliance.go`, `frontend/src/features/build-catalog/` | ⏳ |
| 11.16 | Союзная казна: пожертвования ресурсов, права расходования лидером/казначеем, ledger пожертвований и расходов | `backend/internal/domain/alliance/treasury.go`, `backend/internal/service/alliance_treasury.go`, `frontend/src/features/alliance/TreasuryPanel.tsx` | ⏳ |
| 11.17 | Союзные баффы: покупка/апгрейд за казну, бонусы строительства/ремонта/добычи/обороны/руин/бензина с caps | `backend/internal/domain/alliance/buffs.go`, `backend/internal/service/alliance_buffs.go`, `shared/catalog/alliance-buffs.ts` | ⏳ |

---

## Фаза 12 — Middleware, роутер, Swagger и API-контракт

| # | Что | Файлы | Статус |
|---|---|---|---|
| 12.1 | Middleware CORS, request id, recoverer, body limit, timeout | `backend/internal/adapter/http/middleware/` | ⏳ |
| 12.2 | Middleware logger production access log: route pattern, status class, response size, panic marker | `backend/internal/adapter/http/middleware/logger.go` | ⏳ |
| 12.3 | Rate limiting по risky routes: auth, build/raid, chat, market, uploads, WS commands | `backend/internal/adapter/http/middleware/ratelimit.go`, `backend/internal/adapter/ws/ratelimit.go` | ⏳ |
| 12.4 | Idempotency keys для небезопасных POST: building placement, raid start, market order, alliance invite | `backend/internal/adapter/http/middleware/idempotency.go`, `backend/internal/adapter/redis/idempotency_store.go` | ⏳ |
| 12.5 | Сборка router с группами `/api/v1/auth`, `/players`, `/world`, `/buildings`, `/economy`, `/monsters`, `/territory`, `/raids`, `/alliances`, `/chat`, `/market`, `/admin`, `/health`, `/metrics`, `/swagger` | `backend/internal/adapter/http/router.go` | ⏳ |
| 12.6 | Swagger/OpenAPI annotations и генерация контракта | `backend/docs/swagger/`, `backend/internal/adapter/http/handler/` | ⏳ |
| 12.7 | Typed frontend API client из OpenAPI или ручной client с contract tests | `frontend/src/shared/api/`, `shared/api/` | ⏳ |
| 12.8 | API compatibility policy: versioning, error shape, pagination, cursor rules, deprecation notes | `docs/architecture/api.md`, `backend/internal/adapter/http/dto/` | ⏳ |
| 12.9 | Unit-тесты middleware/router smoke/OpenAPI freshness | `backend/internal/adapter/http/middleware/tests/`, `backend/internal/adapter/http/router_test.go` | ⏳ |

---

## Фаза 13 — Администрирование и модерация

| # | Что | Файлы | Статус |
|---|---|---|---|
| 13.1 | Domain admin/audit: admin roles, audit actions, moderation actions | `backend/internal/domain/admin/`, `backend/internal/domain/audit/` | ⏳ |
| 13.2 | Миграции admin_audit_log/moderation_events/system_settings | `backend/db/migrations/` | ⏳ |
| 13.3 | `service/admin`: list players, get player, deactivate/activate, set admin, force logout | `backend/internal/service/admin.go` | ⏳ |
| 13.4 | Admin world overview: chunks, buildings, resources, monsters, active raids, online players | `backend/internal/service/admin_world.go` | ⏳ |
| 13.5 | Moderation: delete chat message, freeze player, resolve abuse report placeholder | `backend/internal/service/moderation.go` | ⏳ |
| 13.6 | System diagnostics: PostgreSQL, Redis, WS gateway, worker status, tick lag, app version/uptime | `backend/internal/service/diagnostics.go` | ⏳ |
| 13.7 | HTTP endpoints admin users/world/moderation/diagnostics/audit | `backend/internal/adapter/http/handler/admin.go` | ⏳ |
| 13.8 | Frontend admin panel: player list, player detail, system status, world debug controls | `frontend/src/features/admin/` | ⏳ |
| 13.9 | Persistent audit logging admin actions без PII/секретов и read-only audit API | `backend/internal/adapter/postgres/audit_repo.go`, `backend/internal/service/admin.go` | ⏳ |
| 13.10 | Unit-тесты admin permissions, audit persistence, moderation safety | `backend/internal/service/tests/admin_test.go`, `frontend/src/features/admin/**/*.test.tsx` | ⏳ |

---

## Фаза 14 — Ассеты, визуальный пайплайн и контент

| # | Что | Файлы | Статус |
|---|---|---|---|
| 14.1 | Формат visual definitions: atlas/frame/footprint/anchor/sortOffset/states/shadow | `shared/assets/visual-def.ts`, `frontend/src/assets/manifest.json` | ⏳ |
| 14.2 | Каталог placeholder-ассетов MVP без копирования чужого IP: terrain, крупные тайлы, resources, oil wells, buildings, ruins, monsters, effects | `frontend/src/assets/`, `docs/art/asset-guidelines.md` | ⏳ |
| 14.3 | Blender export convention: фиксированная камера, размеры, naming, states, shadows | `docs/art/blender-pipeline.md`, `tools/assets/` | ⏳ |
| 14.4 | Texture atlas build: packing sprites, JSON metadata generation, cache busting | `tools/assets/atlas/`, `frontend/src/assets/atlases/` | ⏳ |
| 14.5 | Asset validation script: missing frames, footprint mismatch, duplicate ids, oversized textures | `tools/assets/validate-assets.ts` или `scripts/validate_assets.go` | ⏳ |
| 14.6 | Runtime asset loader: Pixi assets init, loading progress, fallback sprites, error reporting | `frontend/src/game/assets/` | ⏳ |
| 14.7 | Content balance files: building costs, resource rates, monster stats, raid cooldowns | `shared/balance/`, `backend/internal/domain/catalog/` | ⏳ |
| 14.8 | Internal content viewer: inspect sprites, anchors, footprints, states and sort order | `frontend/src/features/devtools/AssetViewer.tsx` | ⏳ |
| 14.9 | Tests/validation для asset manifests and balance schema | `frontend/src/game/assets/**/*.test.ts`, `shared/**/*.test.ts` | ⏳ |
| 14.10 | Документ IP boundaries: нельзя использовать gnomgrad names/images/texts, правила placeholder и финального контента | `docs/art/ip-boundaries.md`, `AGENTS.md` | ⏳ |
| 14.11 | Модели уровней построек: отдельный visual для каждого уровня и апгрейда, включая жилье, ратушу, Союзный дом, заводы, дороги, поля/грядки, руины | `frontend/src/assets/buildings/`, `frontend/src/assets/manifest.json`, `docs/art/asset-guidelines.md` | ⏳ |
| 14.12 | Ассеты нефтяной цепочки: нефтяная скважина, нефть, бензин, Нефтеперерабатывающий завод, fuel indicators без мрачной индустриальности | `frontend/src/assets/resources/`, `frontend/src/assets/buildings/industry/` | ⏳ |
| 14.13 | Ассеты эолийских кристаллов: вытянутые тонкие шестиугольные аметистовые кристаллы для UI, карты и магазина | `frontend/src/assets/resources/aeolian-crystals/`, `frontend/src/features/hud/` | ⏳ |

---

## Фаза 15 — Кэширование, производительность и масштабирование

| # | Что | Файлы | Статус |
|---|---|---|---|
| 15.1 | Redis cache для chunk snapshots, player state summaries, catalog/balance, territory overlays | `backend/internal/adapter/redis/game_cache.go` | ⏳ |
| 15.2 | Инвалидация кэша при изменении зданий/ресурсов/территории/боёв | `backend/internal/service/cache_keys.go`, `backend/internal/service/events.go` | ⏳ |
| 15.3 | Spatial query optimization: chunk indexes, bounding boxes, hot viewport queries | `backend/db/migrations/`, `backend/db/query/world.sql` | ⏳ |
| 15.4 | Frontend render performance: sprite pooling, culling, batched updates, texture atlas usage, крупные тайлы без лишней overdraw | `frontend/src/game/renderers/`, `frontend/src/game/performance/` | ⏳ |
| 15.5 | Network performance: event coalescing, viewport diff compression, heartbeat tuning | `backend/internal/adapter/ws/`, `frontend/src/shared/realtime/` | ⏳ |
| 15.6 | Load tests: chunk load, WS fanout, placement commands, simulation ticks, chat throughput | `tests/k6/`, `tests/ws-load/` | ⏳ |
| 15.7 | Profiling hooks: pprof in non-public admin/internal route, frontend performance marks | `backend/internal/adapter/http/handler/debug.go`, `frontend/src/game/performance/marks.ts` | ⏳ |
| 15.8 | Graceful degradation: Redis unavailable, WS reconnect storms, slow DB, asset load failure | `backend/internal/service/`, `frontend/src/app/` | ⏳ |
| 15.9 | Unit/integration tests cache-aside, invalidation, degraded fallback | `backend/internal/adapter/redis/tests/`, `backend/internal/service/tests/cache_test.go` | ⏳ |
| 15.10 | Логирование performance/cache: hit/miss/set/delete, slow queries, slow ticks, dropped events, FPS/runtime warnings | `backend/internal/adapter/redis/`, `backend/internal/worker/`, `frontend/src/game/performance/` | ⏳ |
| 15.11 | Срочная оптимизация карты: найден и исправлен bottleneck DOM-отрисовки тысяч тайлов, terrain перенесён в Pixi canvas, React оставлен для UI/оверлеев | `frontend/src/game/IsoMap.tsx`, `frontend/src/game/renderer/PixiStage.tsx`, `frontend/src/features/world/useVisibleChunks.ts` | ✅ |
| 15.12 | Incremental rendering: не перерисовывать всю карту при каждом изменении, dirty chunks/tiles, partial updates и стабильные display objects | `frontend/src/game/renderers/`, `frontend/src/features/world/realtime.ts` | ⏳ |
| 15.13 | Data loading optimization: минимальный payload viewport, cursor/version diff, сжатие больших списков объектов, lazy details для inspector | `backend/internal/adapter/http/handler/world.go`, `backend/internal/service/world.go`, `frontend/src/shared/api/world.ts` | ⏳ |
| 15.14 | Performance tests для цикличной крупнотайловой карты: pan через границу мира, zoom, загрузка швов, 60s scroll soak | `frontend/tests/performance/map.spec.ts`, `backend/internal/service/tests/world_wrap_test.go` | ⏳ |

---

## Фаза 16 — Тестирование и качество

| # | Что | Файлы | Статус |
|---|---|---|---|
| 16.1 | Backend unit-тесты всех доменных правил: placement, economy, combat, territory, AI, cooldowns | `backend/internal/domain/**/*_test.go` | ⏳ |
| 16.2 | Backend service unit-тесты с fake repositories/cache/event bus | `backend/internal/service/**/*_test.go` | ⏳ |
| 16.3 | Интеграционные тесты PostgreSQL/Redis через testcontainers-go: миграции, репозитории, locks, constraints | `backend/internal/adapter/postgres/tests/`, `backend/internal/adapter/redis/tests/` | ⏳ |
| 16.4 | API smoke/e2e compose tests: auth → world → build → economy → realtime → monster → raid | `tests/e2e/api/` | ⏳ |
| 16.5 | Frontend unit/component tests для stores, panels, render state reducers, API client | `frontend/src/**/*.test.ts`, `frontend/src/**/*.test.tsx` | ⏳ |
| 16.6 | Playwright E2E playable MVP: login, load map, place building, wait completion, harvest resource, receive WS event | `frontend/tests/e2e/` | ⏳ |
| 16.7 | Visual regression/screenshot tests: desktop/mobile, placement, inspector states, combat/monster overlays | `frontend/tests/visual/` | ⏳ |
| 16.8 | Static quality gates: eslint, prettier, typecheck, gofmt, go vet, golangci-lint, dependency audit | `frontend/package.json`, `backend/Makefile`, `.github/workflows/ci.yml` | ⏳ |
| 16.9 | Manual QA checklist для playable MVP и регрессий realtime | `docs/qa/playable-mvp.md` | ⏳ |

---

## Фаза 17 — Observability

| # | Что | Файлы | Статус |
|---|---|---|---|
| 17.1 | Middleware metrics: Prometheus `/metrics`, HTTP latency, WS connections, commands, errors, in-flight requests | `backend/internal/adapter/http/middleware/metrics.go`, `backend/internal/adapter/ws/metrics.go` | ⏳ |
| 17.2 | Simulation metrics: tick duration, actions processed, queue lag, lock contention, failed ticks | `backend/internal/worker/simulation/metrics.go` | ⏳ |
| 17.3 | Game metrics: active players, loaded chunks, buildings placed, resources produced/spent, raids, monsters | `backend/internal/service/metrics.go` | ⏳ |
| 17.4 | Panic/error reporting middleware: recovery marker, stack trace в dev, безопасный error event в prod; optional Sentry | `backend/internal/adapter/http/middleware/recover.go`, `backend/pkg/config/config.go` | ⏳ |
| 17.5 | Frontend telemetry: runtime errors, WS reconnects, asset load failures, FPS warnings без персональных данных | `frontend/src/shared/telemetry/`, `frontend/src/game/performance/` | ⏳ |
| 17.6 | Инфраструктура логов/метрик: Loki/Promtail или Docker logging driver, Prometheus, Grafana dashboards | `deploy/observability/`, `docker-compose.observability.yml` | ⏳ |
| 17.7 | Dashboards/runbooks: slow requests, WS degradation, simulation lag, Redis/DB issues, frontend blank canvas | `docs/operations/observability.md`, `deploy/observability/` | ⏳ |

---

## Фаза 18 — Деплой и runtime-инфраструктура

| # | Что | Файлы | Статус |
|---|---|---|---|
| 18.1 | Backend Dockerfile: multi-stage build, non-root runtime, CA certificates, healthcheck | `backend/Dockerfile` | ⏳ |
| 18.2 | Frontend Dockerfile/nginx: React build, SPA fallback, static asset cache headers | `frontend/Dockerfile`, `frontend/nginx.conf` | ⏳ |
| 18.3 | Production compose: frontend, backend, postgres, redis, worker, volumes, healthchecks, restart policies, private networks | `docker-compose.yml`, `docker-compose.prod.yml` | ⏳ |
| 18.4 | Prod env-шаблон: обязательные секреты, CORS, JWT TTL, DB/Redis DSN, public URLs, simulation limits | `.env.prod.example`, `backend/.env.prod.example`, `frontend/.env.production.example` | ⏳ |
| 18.5 | Nginx reverse proxy: HTTPS termination, HTTP→HTTPS redirect, `/api/*`, `/ws`, SPA fallback, upload/body/timeout limits | `deploy/nginx/nginx.conf`, `docs/operations/deploy.md` | ⏳ |
| 18.6 | Операционные команды: migrate, seed dev, backup/restore DB, deploy, rollback, logs, shell | `Makefile`, `scripts/`, `docs/operations/deploy.md` | ⏳ |
| 18.7 | Security hardening: secure headers, cookie/token policy, admin endpoints restricted, metrics/internal protection | `deploy/nginx/`, `backend/internal/adapter/http/middleware/`, `docs/operations/security.md` | ⏳ |
| 18.8 | Runtime validation checklist: cold start, migration, WS through proxy, static assets, health/readiness, graceful shutdown | `docs/operations/deploy.md`, `tests/e2e/deploy-smoke.md` | ⏳ |

---

## Фаза 19 — CI/CD

| # | Что | Файлы | Статус |
|---|---|---|---|
| 19.1 | GitHub Actions CI frontend: install, lint, typecheck, unit tests, build | `.github/workflows/frontend-ci.yml` | ⏳ |
| 19.2 | GitHub Actions CI backend: gofmt check, go vet, golangci-lint, unit tests, build | `.github/workflows/backend-ci.yml` | ⏳ |
| 19.3 | Integration CI: docker compose services, migrations, API smoke, Playwright smoke | `.github/workflows/integration.yml` | ⏳ |
| 19.4 | Docker pipeline: build frontend/backend images, scan, tag by commit/version, push по main/tag | `.github/workflows/docker.yml` | ⏳ |
| 19.5 | Contract freshness checks: OpenAPI generated, shared types/catalog schemas current | `.github/workflows/contract.yml`, `scripts/check_contracts.sh` | ⏳ |
| 19.6 | CD-процесс: manual approval, deploy/rollback workflow или documented deployment для выбранного стенда | `.github/workflows/deploy.yml`, `docs/operations/deploy.md` | ⏳ |

---

## Фаза 20 — Финальная документация

| # | Что | Файлы | Статус |
|---|---|---|---|
| 20.1 | README проекта: назначение, стек, быстрый старт, команды, архитектура, ссылки на документацию | `README.md` | ⏳ |
| 20.2 | Product overview: сеттинг, core loop, карта, экономика, PvE/PvP, ограничения MVP | `docs/product/overview.md` | ⏳ |
| 20.3 | User guide: регистрация, карта, строительство, ресурсы, защита, монстры, рейды, чат/союзы, рынок | `docs/product/user-guide.md` | ⏳ |
| 20.4 | Architecture docs: backend, frontend, realtime, simulation, storage, asset pipeline, deployment | `docs/architecture/` | ⏳ |
| 20.5 | API reference: OpenAPI, WS protocol, event catalog, error model, pagination/versioning | `docs/api/`, `backend/docs/swagger/` | ⏳ |
| 20.6 | Operations docs: deploy, observability, troubleshooting, backup/restore, security | `docs/operations/` | ⏳ |
| 20.7 | Game design docs: balance tables, building/resource/monster catalog, IP boundaries, future roadmap | `docs/game-design/`, `shared/balance/` | ⏳ |
| 20.8 | Финальный паспорт playable MVP: реализованные функции, known limitations, проверочный чеклист, demo scenario | `docs/final-mvp.md` | ⏳ |
| 20.9 | Синхронизация design docs с сеттингом Эолии: монеты, эолийские кристаллы, нефть/бензин, жилье, поля/грядки, Союзный дом, цикличный мир | `docs/visual-style-and-setting-options.md`, `docs/game-design/setting.md`, `docs/product/overview.md` | ⏳ |

## Порядок зависимостей

```
Фаза 0 (каркас)
    ├── Фаза 1 (аккаунты, игроки и сессии)
    │       ├── Фаза 2 (мировая карта, координаты и чанки)
    │       │       ├── Фаза 3 (игровой HUD и базовый UI) — параллельно с базовым рендером карты
    │       │       ├── Фаза 4 (здания, размещение и строительство)
    │       │       │       ├── Фаза 5 (экономика, ресурсы и инвентарь)
    │       │       │       │       └── Фаза 7 (симуляция мира, таймеры и фоновые задачи)
    │       │       │       ├── Фаза 9 (территория, владение и защита)
    │       │       │       │       └── Фаза 10 (PvP, рейды, разрушения и ремонт)
    │       │       │       └── Фаза 15 (кэширование, производительность и масштабирование)
    │       │       └── Фаза 8 (монстры, PvE и угрозы) — после базовой карты, чанков и simulation worker
    │       └── Фаза 11 (союзы, чат, рынок и социальные механики)
    ├── Фаза 6 (Realtime WebSocket и события мира) — после auth и базовой карты; затем используется фазами 4–11
    ├── Фаза 12 (middleware, роутер, Swagger и API-контракт) — параллельно с 1–11, но финализируется после стабилизации API
    └── Фаза 14 (ассеты, визуальный пайплайн и контент) — параллельно frontend/gameplay фазам, критична до polished MVP

Фаза 13 (администрирование и модерация) — после auth, world, realtime и базовых gameplay-сущностей; diagnostics зависят от 7, 15 и 17.
Фаза 16 (тестирование и качество) — наращивается по всем фазам, финальный проход после завершения прикладных фаз 1–15.
Фаза 17 (observability) — после базового logger из 0 и realtime/simulation из 6–7; инфраструктура нужна до production-like деплоя.
Фаза 18 (деплой и runtime-инфраструктура) — после стабилизации сборки frontend/backend, миграций, WS proxy и observability.
Фаза 19 (CI/CD) — после фиксации команд тестирования, сборки, contract generation и docker pipeline.
Фаза 20 (финальная документация) — последняя, после фиксации фактических функций, API, запуска, деплоя и пользовательских сценариев.
Ближайший playable MVP: фазы 0–8 с минимальной частью 9, 12, 14, 15, 16 и 17; PvP, союзы, рынок и production hardening выполняются после доказательства server-authoritative flow.
```
