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

`make create-test-admin` запускает отдельную тестовую базу и создаёт администратора
`admin@example.com` с паролем `admin12345`. Баланс каждого ресурса, включая монеты,
устанавливается не ниже 2 000 000 000. Повторный запуск пополняет потраченные ресурсы.
Для других учётных данных задайте `ADMIN_EMAIL`, `ADMIN_NAME` и `ADMIN_PASSWORD`.
Тестовый API запускается командой `make test-backend-up` на порту 18080.

## Локальная наблюдаемость

Prometheus и Grafana запускаются отдельным Compose overlay только по явной команде:

```bash
make observability-up
make observability-targets
make observability-down
bash scripts/check-observability.sh
```

Prometheus: <http://127.0.0.1:9090/targets>. Grafana: <http://127.0.0.1:3000/>; начальный вход `admin` / `admin`. Перед запуском можно задать `GRAFANA_ADMIN_USER` и `GRAFANA_ADMIN_PASSWORD` в окружении. Данные сохраняются в Compose volumes после `observability-down`. Проверка конфигурации использует Docker для `promtool`, если он не установлен локально. Подробности, включая worker, диагностику панелей и базовую линию, описаны в [руководстве по наблюдаемости](docs/operations/observability.md).
