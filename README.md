# Real City

`Real City` - браузерная multiplayer-стратегия на одной общей постоянной карте.

## Структура

- `backend/` - авторитетный Go API, realtime gateway и будущая симуляция мира.
- `frontend/` - Vite + React + TypeScript клиент с игровой картой первым экраном.
- `shared/` - общие TypeScript-контракты для координат, чанков, объектов, событий и API-ошибок.
- `docs/` - планы и проектная документация.
- `reference/` - локальные референсы механик и визуального направления.

## Команды разработки

```bash
make test
make backend-test
make frontend-test
make backend-run
make backend-run-local
make frontend-dev
```

Для локальной инфраструктуры:

```bash
make backend-up
make backend-down
make db-up
make migrate-up
make migrate-down
make migrate-status
make create-test-admin
```
