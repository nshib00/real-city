# Обзор фронтенда

## Стек

| Область | Используется | Где смотреть |
| --- | --- | --- |
| Сборка | Vite 6 | `frontend/vite.config.ts` |
| UI | React 19 | `frontend/src/main.tsx`, `frontend/src/app/App.tsx` |
| Язык | TypeScript | `frontend/tsconfig.json` |
| Серверное состояние | TanStack React Query | `frontend/src/app/providers/queryClient.ts`, `frontend/src/shared/api/` |
| Клиентское состояние карты | Zustand | `frontend/src/game/state/useGameStore.ts` |
| 2D-рендер тайлов | Pixi.js | `frontend/src/game/renderer/PixiStage.tsx` |
| 3D-модели зданий | Three.js + GLTFLoader | `frontend/src/game/renderers/BuildingGlbModel.tsx` |
| Иконки UI | lucide-react | Компоненты в `frontend/src/features/**` и `frontend/src/shared/ui/` |
| Тесты | Vitest + Testing Library, отдельный Playwright smoke | `frontend/src/**/*.test.*`, `frontend/tests/e2e/ui.spec.ts` |

Команды из `frontend/package.json`:

```bash
npm run dev
npm run build
npm run test
npm run lint
```

`npm run lint` в этом проекте фактически запускает TypeScript-проверку `tsc --noEmit`.

## Точка входа

`frontend/src/main.tsx` монтирует React-приложение в `#root`, подключает `QueryClientProvider` и глобальные стили:

- `frontend/src/app/styles/index.css` - основная визуальная система, панели, карта, кнопки, дроуеры, карточки;
- `frontend/src/app/styles/layout.css` - адаптивные правила для планшетов и мобильных экранов.

`frontend/src/app/App.tsx` собирает весь игровой экран. Важная особенность: часть компонентов ничего не рисует, а только синхронизирует данные.

Верхний уровень выглядит так:

```tsx
<ErrorBoundary>
  <AuthGate>
    <main className="game-shell">
      <ResourceBar />
      <ProfilePanel />
      <ToolBar />
      <MapWidget />
      <BuildMenu />
      <BuildingSync />
      <ResourceNodeSync />
      <MonsterSync />
      <WorldRealtime />
      <ConstructionTicker />
      <IsoMap />
      <Inspector />
      <ProductionPanel />
      <EventLog />
      <NotificationCenter />
      <ResourceRegistry />
      <AlliancePanel />
    </main>
  </AuthGate>
</ErrorBoundary>
```

## Структура каталогов

| Каталог | Назначение |
| --- | --- |
| `frontend/src/app` | Корень приложения, ErrorBoundary, провайдеры, глобальные стили |
| `frontend/src/features` | Фичи пользовательского интерфейса и игровой логики вокруг конкретных сценариев |
| `frontend/src/game` | Карта, изометрические координаты, рендер, игровые модели, Zustand-store |
| `frontend/src/shared` | Общие API-клиенты, realtime-клиент, контракты, базовые UI-компоненты |
| `frontend/src/assets` | Ассеты, импортируемые сборщиком, в основном GLB и README по наборам |
| `frontend/public/assets` | Публичные PNG/JSON ассеты, доступные по URL `/assets/...` |
| `frontend/src/stories` | Storybook-like/демо-истории интерфейса, сейчас без отдельной команды запуска |
| `frontend/tests/e2e` | E2E smoke-тесты Playwright |

`frontend/node_modules` и `frontend/dist` являются сгенерированными каталогами и не считаются исходной структурой проекта.

## Состояние приложения

Есть два основных типа состояния:

1. Серверное состояние через React Query: инвентарь, здания, чанки мира, ресурсы, монстры, угрозы, производство, союзы, рынок, чат.
2. Клиентское состояние через Zustand: выбранный тайл/объект, режим инструмента, камера, viewport, локальные списки объектов карты, открытые панели.

Zustand-store `frontend/src/game/state/useGameStore.ts` хранит:

- активный инструмент: `select`, `build`, `road`, `repair`, `raid`;
- выбранный тайл, здание, монстр и hover-тайл;
- массивы `buildings`, `resourceNodes`, `monsters`, `worldTiles`;
- таймер строительства `constructionNow`;
- камеру `x/y/zoom`;
- viewport-центр и радиус;
- UI-предпочтения: компактные панели, открыт ли реестр ресурсов, союзная панель и меню строительства;
- realtime-статус подключения.

## Ошибки и защита UI

`frontend/src/app/ErrorBoundary.tsx` ловит исключения React-дерева, пишет событие в `console.error('ui.error_boundary', ...)` и показывает пользователю простой статус `Интерфейс временно недоступен`.

Авторизация находится выше игрового экрана: `AuthGate` не показывает игру, пока пользователь не вошел или пока не восстановлена сессия.

## Прокси API

`frontend/vite.config.ts` проксирует все запросы `/api` на backend:

- по умолчанию `http://localhost:8080`;
- можно переопределить через `VITE_API_PROXY_TARGET`.

Фронтенд всегда вызывает API относительными путями `/api/v1/...`, поэтому в dev-режиме достаточно прокси Vite.
