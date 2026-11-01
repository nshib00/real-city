# Тестирование фронтенда

## Команды

Из каталога `frontend/`:

```bash
npm run test
npm run lint
npm run build
```

Из корня репозитория можно запускать команды с указанием каталога:

```bash
npm --prefix frontend run test
npm --prefix frontend run lint
npm --prefix frontend run build
```

`npm run test` запускает Vitest. Конфигурация находится в `frontend/vite.config.ts`:

- environment: `jsdom`;
- исключены `node_modules/**`, `dist/**`, `tests/e2e/**`;
- включены globals.

`npm run lint` запускает `tsc --noEmit`.

## Покрытые области

| Область | Тесты |
| --- | --- |
| API-клиент | `frontend/src/shared/api/client.test.ts` |
| Auth API | `frontend/src/features/auth/api.test.ts` |
| Social API | `frontend/src/shared/api/social.test.ts` |
| Store игры | `frontend/src/game/state/useGameStore.test.ts` |
| Изометрические координаты | `frontend/src/game/coordinates/iso.test.ts` |
| Видимость объектов | `frontend/src/game/renderer/visibleObjects.test.ts` |
| Текстуры terrain | `frontend/src/game/renderer/terrainTextures.test.ts` |
| Правила placement | `frontend/src/features/build-placement/placement.test.ts` |
| Каталог/меню строительства | `frontend/src/features/buildings/BuildMenu.test.tsx` |
| Инспектор | `frontend/src/features/inspector/Inspector.test.tsx` |
| Верхняя панель ресурсов | `frontend/src/features/hud/ResourceBar.test.tsx` |
| Реестр ресурсов | `frontend/src/features/resources/ResourceRegistry.test.tsx` |
| Иконки ресурсов | `frontend/src/features/resources/ResourceIcon.test.ts` |
| Производство | `frontend/src/features/production/ProductionPanel.test.ts` |
| Профиль | `frontend/src/features/player/ProfilePanel.test.tsx` |
| Панель инструментов | `frontend/src/features/tools/ToolBar.test.tsx` |
| Мини-карта | `frontend/src/features/world-map/MapWidget.test.tsx` |
| Лесные действия | `frontend/src/features/world/forestActions.test.ts` |
| Realtime application logic | `frontend/src/features/world/realtime.test.ts` |
| Рендереры зданий и ресурсов | `frontend/src/game/renderers/*.test.ts` |

## E2E smoke и визуальный gate

Файл: `frontend/tests/e2e/ui.spec.ts`.

Тесты проверяют:

- что на desktop видны карта, ресурсы, инструменты и инспектор;
- что на mobile основные элементы остаются доступными.

В тесте мокируются:

- токены в `localStorage`;
- `/api/v1/players/me`;
- `/api/v1/world/chunks`.

Playwright закреплён в `frontend/package.json`. `playwright.rollout.config.ts` проверяет, что переключение `aeolian` ↔ `classic` не размонтирует карту, не теряет фокус/выделение/черновик чата и не создаёт игровые mutation-запросы. Pixel baselines этой пары тем запускаются в workflow `browser-e2e` на 390 и 1440 px. Намеренное изменение внешнего вида требует локального просмотра дифа и обновления baseline той же версией Chromium; не обновлять снимки автоматически в CI.

Дополнительные матрицы доступны через `playwright.review.config.ts` (320–1440 px, DPR 1/2, landscape); сценарии карты и live сервера — в `tests/e2e/`. E2E-каталог исключён из Vitest и запускается отдельной конфигурацией Playwright.

Для pull request frontend CI запускает TypeScript-проверку, unit-тесты, production build и бюджет UI/runtime ассетов. Browser CI выполняет изолированный интерфейсный smoke, rollout snapshot gate и отдельную live API/WS матрицу desktop/mobile. CI-эмуляция не заменяет физический телефон, настоящий скринридер и независимый просмотр визуальных дифов.

## Что полезно проверять при изменениях

При изменении UI-компонента:

```bash
npm --prefix frontend run test
npm --prefix frontend run lint
```

При изменении карты, рендера, координат, ассетов:

```bash
npm --prefix frontend run test
npm --prefix frontend run build
```

При изменении API-контрактов:

```bash
npm --prefix frontend run lint
npm --prefix frontend run test
```

## Зоны риска

- `BuildingKind` в `useGameStore.ts` должен быть согласован с `shared/catalog/buildings.ts` и backend-каталогом.
- `frontend/src/features/buildings/catalog.ts` показывает только `firstLevel` из общего каталога, поэтому новые апгрейд-ветки могут не появиться в меню строительства.
- Визуальная поддержка здания требует отдельного подключения в `IsoMap.tsx` и renderers.
- Realtime-события обновляют Zustand и инвалидируют React Query; при добавлении нового типа события нужно не забыть оба действия.
- E2E smoke лежит отдельно от Vitest и выполняется в workflow `browser-e2e`.
