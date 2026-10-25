# Карта функций фронтенда

Этот файл отвечает на вопрос “где реализована конкретная функция интерфейса или игровой механики”.

## Авторизация и профиль

| Функция | Где реализована | Что делает |
| --- | --- | --- |
| Проверка сессии при старте | `frontend/src/features/auth/AuthGate.tsx` | Если есть access token, пробует `/players/me`, затем refresh; иначе показывает экран входа |
| Вход и регистрация | `frontend/src/features/auth/AuthScreen.tsx` | Форма логина/регистрации, отправка, показ ошибок |
| Auth API | `frontend/src/features/auth/api.ts` | `register`, `login`, `refresh`, `logout`, `getMe`, `updateMe`, `changePassword` |
| Auth store | `frontend/src/features/auth/useAuthStore.ts` | Хранит `player` и `isAuthenticated` |
| Типы игрока | `frontend/src/features/auth/types.ts` | `Player`, `PlayerProfile`, настройки уведомлений и качества рендера |
| Профиль в интерфейсе | `frontend/src/features/player/ProfilePanel.tsx` | Кнопка профиля, дроуер профиля, настройки, выход |

Токены хранятся в `localStorage` с ключами `real-city.access-token` и `real-city.refresh-token`. Низкоуровневая работа с токенами находится в `frontend/src/shared/api/client.ts`.

## Игровая оболочка

| Функция | Где реализована |
| --- | --- |
| Композиция игрового экрана | `frontend/src/app/App.tsx` |
| Основной layout и панели | `frontend/src/app/styles/index.css` |
| Адаптивное поведение | `frontend/src/app/styles/layout.css` |
| Верхняя панель ресурсов | `frontend/src/features/hud/ResourceBar.tsx` |
| Панель инструментов | `frontend/src/features/tools/ToolBar.tsx` |
| Мини-карта и переход к ратуше | `frontend/src/features/world-map/MapWidget.tsx` |
| Инспектор тайла/объекта/игрока | `frontend/src/features/inspector/Inspector.tsx` |
| Уведомления | `frontend/src/features/notifications/NotificationCenter.tsx` |
| Журнал событий и чат | `frontend/src/features/event-log/EventLog.tsx`, `frontend/src/features/chat/ChatPanel.tsx` |

`NotificationCenter` сейчас использует статический список уведомлений, а не серверные события. `EventLog` тоже содержит статические события, но вкладка `Чат` уже подключена к API.

## Карта и навигация

| Функция | Где реализована | Детали |
| --- | --- | --- |
| Изометрическая карта | `frontend/src/game/IsoMap.tsx` | Собирает Pixi-тайлы, DOM-объекты, выбор тайлов, drag-pan, zoom |
| Pixi-рендер тайлов | `frontend/src/game/renderer/PixiStage.tsx` | Рисует текстурированные тайлы и overlay выбранного/hover-тайла |
| Изометрические координаты | `frontend/src/game/coordinates/iso.ts` | `gridToScreen`, `screenToGrid`, `tileToChunk`, wrap мира |
| Видимые объекты | `frontend/src/game/renderer/visibleObjects.ts` | Фильтрация объектов по viewport |
| Загрузка чанков | `frontend/src/features/world/useVisibleChunks.ts` | React Query hook для `/world/chunks` |
| Рубка леса | `frontend/src/features/world/forestActions.ts`, `IsoMap.tsx` | Если выбран лесной тайл, отправляется `chopForest` |

Мир имеет wrap по координатам: `WORLD_WRAP_TILES = 160`. Камера перемещается непрерывно; `wrapGridCoord` нормализует координаты клеток, а `nearestWrappedScreenCoord` выбирает ближайшее видимое повторение клетки.

## Строительство

| Функция | Где реализована |
| --- | --- |
| Меню строительства | `frontend/src/features/buildings/BuildMenu.tsx` |
| UI-каталог строительства | `frontend/src/features/buildings/catalog.ts` |
| Синхронизация зданий с API | `frontend/src/features/buildings/BuildingSync.tsx` |
| Локальный тик завершения строительства | `frontend/src/features/buildings/ConstructionTicker.tsx` |
| Валидация предпросмотра размещения | `frontend/src/features/build-placement/placement.ts` |
| API зданий | `frontend/src/shared/api/buildings.ts` |
| Баланс и характеристики построек | `shared/catalog/buildings.ts` |

`BuildMenu` показывает только первые уровни построек: `frontend/src/features/buildings/catalog.ts` фильтрует общий каталог по `firstLevel`. Описания для карточек строительства пока задаются отдельно во фронтовом `descriptions`.

Размещение проверяется на фронте для подсказок и UX:

- нужен выбранный тайл;
- ратуша должна быть первой постройкой;
- ратуша может быть только одна;
- нельзя ставить на занятую клетку;
- нельзя ставить на клетку с монстром;
- нельзя строить на лесу, воде, горах, руинах и нефтяных скважинах.

Сервер все равно остается авторитетным источником правил. Фронтовая валидация нужна для раннего сообщения пользователю.

## Инспектор и действия с объектами

`frontend/src/features/inspector/Inspector.tsx` - центральная панель действий.

Инспектор показывает:

- выбранный тайл, hover-тайл, чанк, тип поверхности;
- густоту леса;
- ресурсный узел на тайле;
- уровень угрозы;
- выбранное здание, здоровье, владельца, статус, таймер стройки;
- выбранного монстра, здоровье, состояние, урон, агро-радиус и цель.

Инспектор запускает действия:

- открыть меню строительства;
- переключить режим `build`/`raid`/`road`;
- улучшить здание через `patchBuilding(id, 'upgrade')`;
- ускорить строительство через `patchBuilding(id, 'rush_complete')`;
- удалить здание через `deleteBuilding`;
- собрать грядку `field_bed` через `harvestWindleafField`;
- атаковать монстра через `attackMonster`.

Расчет следующего улучшения для UI находится в том же файле в функциях `getNextUpgrade`, `upgradeComparisons`, `getCurrentStats`.

## Ресурсы и экономика

| Функция | Где реализована |
| --- | --- |
| Инвентарь | `frontend/src/features/economy/useInventory.ts` |
| Верхняя строка ресурсов | `frontend/src/features/hud/ResourceBar.tsx` |
| Реестр всех ресурсов | `frontend/src/features/resources/ResourceRegistry.tsx` |
| Иконки ресурсов | `frontend/src/features/resources/ResourceIcon.tsx` |
| Расчеты лимитов и значений | `frontend/src/features/resources/resourceAmounts.ts` |
| Синхронизация ресурсных узлов | `frontend/src/features/resources/ResourceNodeSync.tsx` |
| Economy API | `frontend/src/shared/api/economy.ts` |

`resourceAmounts.ts` считает:

- лимит населения по активным housing-постройкам;
- лимит монет из `coin_capacity`;
- общий лимит построек по уровню ратуши;
- использованный лимит построек, где дороги не учитываются.

`ResourceRegistry` содержит справочный список ресурсов с категориями, fallback-значениями, лимитами и источниками. Это UI-справочник, не серверный баланс.

## Производство и поля

| Функция | Где реализована |
| --- | --- |
| Производственная панель | `frontend/src/features/production/ProductionPanel.tsx` |
| Рецепты производства | `listProductionRecipes` в `frontend/src/shared/api/economy.ts` |
| Задачи производства | `listProductionJobs`, `startProduction`, `patchProductionJob` |
| Стадии роста поля | `frontend/src/features/fields/fieldGrowth.ts` |
| Сбор ветролиста | `harvestWindleafField` в `frontend/src/shared/api/economy.ts` |

`ProductionPanel` загружает рецепты и задачи, показывает входные ресурсы рецептов, запускает производство и позволяет собрать или отменить задачу. Сейчас `building_id` при запуске передается как `recipe.building_type`; если backend ожидает ID конкретной постройки, это место нужно будет доработать.

## Монстры и угрозы

| Функция | Где реализована |
| --- | --- |
| Синхронизация монстров | `frontend/src/features/monster/MonsterSync.tsx` |
| API монстров | `frontend/src/shared/api/monsters.ts` |
| Уровень угрозы выбранного тайла | `frontend/src/features/threat/ThreatPanel.tsx` |
| Подписи и CSS-классы монстров | `frontend/src/game/renderers/monsters.ts` |
| Атака монстра | `Inspector.tsx` через `attackMonster` |

`MonsterSync` опрашивает сервер каждые 8 секунд вокруг текущего viewport. Realtime-события монстров дополнительно применяются через `features/world/realtime.ts`.

## Союзы, рынок и чат

| Функция | Где реализована |
| --- | --- |
| Союзный дом | `frontend/src/features/alliance/AlliancePanel.tsx` |
| Социальный API | `frontend/src/shared/api/social.ts` |
| Создание союза | `createAlliance` |
| Казна и пожертвования | `donateToAlliance` |
| Баффы союза | `upgradeAllianceBuff` |
| Рынок | `listMarketOrders`, `createMarketOrder`, `cancelMarketOrder` |
| Чат | `frontend/src/features/chat/ChatPanel.tsx` |

`AlliancePanel` открывается из верхней панели ресурсов кнопкой `Союз`. Панель умеет создавать союз, показывать участников, принимать пожертвования, прокачивать локально описанные баффы и выставлять рыночные ордера.

`ChatPanel` доступен через вкладку `Чат` в `EventLog`, опрашивает сообщения каждые 5 секунд и отправляет новые сообщения.

## Небольшие доменные помощники

| Файл | Назначение |
| --- | --- |
| `frontend/src/features/population/population.ts` | Тип `PopulationSummary` и расчет занятого населения |
| `frontend/src/features/presence/presence.ts` | Обновление presence-списка игрока |
| `frontend/src/features/fields/fieldGrowth.ts` | Стадии роста ветролиста и шанс супер-урожая |

`frontend/src/features/territory` сейчас пустой каталог. Судя по названию, это место под будущую UI-логику территории, границ и влияния.

## Общие UI-компоненты

| Компонент | Где находится | Назначение |
| --- | --- | --- |
| `IconButton` | `frontend/src/shared/ui/IconButton.tsx` | Иконка-кнопка с `title`, `aria-label`, `aria-pressed` |
| `Drawer` | `frontend/src/shared/ui/Drawer.tsx` | Боковая панель справа или слева |
| `Modal` | `frontend/src/shared/ui/Modal.tsx` | Модальное окно с backdrop |
| `Tabs` | `frontend/src/shared/ui/Tabs.tsx` | Вкладки с badge |
| `SegmentedControl` | `frontend/src/shared/ui/SegmentedControl.tsx` | Переключатель режимов/категорий |
| `StatusState` | `frontend/src/shared/ui/StatusState.tsx` | Простое состояние загрузки/ошибки |

Экспорт всех базовых UI-компонентов собран в `frontend/src/shared/ui/index.ts`.
