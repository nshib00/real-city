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

## E2E smoke

Файл: `frontend/tests/e2e/ui.spec.ts`.

Тесты проверяют:

- что на desktop видны карта, ресурсы, инструменты и инспектор;
- что на mobile основные элементы остаются доступными.

В тесте мокируются:

- токены в `localStorage`;
- `/api/v1/players/me`;
- `/api/v1/world/chunks`.

Важно: `@playwright/test` не указан в `frontend/package.json`, а e2e-каталог исключен из Vitest. Для запуска этих тестов нужна отдельная настройка Playwright в проекте или workspace-уровне.

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
- E2E smoke лежит отдельно от обычного test pipeline.
