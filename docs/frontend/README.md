# Документация фронтенда

Этот раздел описывает устройство проекта `frontend`: где лежат основные части интерфейса, как данные проходят от API до карты и панелей, где реализованы игровые функции, рендер, ассеты и тесты.

## Быстрые ссылки

| Файл | О чем |
| --- | --- |
| [overview.md](overview.md) | Общая архитектура, стек, точка входа, структура каталогов |
| [features.md](features.md) | Где реализованы пользовательские и игровые функции |
| [api-and-realtime.md](api-and-realtime.md) | REST API, авторизация, React Query, WebSocket-синхронизация |
| [rendering-and-assets.md](rendering-and-assets.md) | Изометрическая карта, Pixi, Three.js/GLB, PNG-ассеты |
| [testing.md](testing.md) | Тесты, команды проверки, что покрыто |

## Главное за одну минуту

Фронтенд находится в `frontend/` и собран на Vite + React + TypeScript. Первый экран после авторизации сразу является игровым интерфейсом: карта, ресурсы, профиль, инструменты, инспектор, производство, журнал событий, уведомления и панели-дроуеры.

Основная композиция интерфейса находится в `frontend/src/app/App.tsx`. Клиентское игровое состояние хранится в Zustand-store `frontend/src/game/state/useGameStore.ts`. Данные с сервера загружаются через React Query и API-модули в `frontend/src/shared/api/`. Realtime-события приходят через WebSocket-клиент `frontend/src/shared/realtime/client.ts` и применяются в `frontend/src/features/world/realtime.ts`.

Карта состоит из двух слоев: тайлы рисуются Pixi.js в `frontend/src/game/renderer/PixiStage.tsx`, а здания, ресурсы и монстры накладываются React/DOM-объектами в `frontend/src/game/IsoMap.tsx`.

Баланс построек для интерфейса берется из общего каталога `shared/catalog/buildings.ts`, а фронтовый список строительства формируется в `frontend/src/features/buildings/catalog.ts`.
