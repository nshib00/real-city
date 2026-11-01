# Очередь 111–120: фактический результат

Дата: 01.11.2026. [Постановка](queue-111-120.md). Работа выполнена в текущем рабочем дереве без изменения существующего тестового мира. Изолированный Compose-проект удалил свои контейнеры и тома после проверки. Изменения не отправлялись в GitHub и не выкладывались на внешний сервер.

| № | Результат |
| --- | --- |
| 111 | `JWT_ACCESS_TTL` и `JWT_REFRESH_TTL` передаются из production Compose; в шаблоне указаны 15 минут и 720 часов. Проверено чтение значений из окружения. |
| 112 | `CORS_ALLOWED_ORIGINS` в production Compose равен `https://DOMAIN`. Router получает список из конфигурации вместо постоянного `*`. При прямом production-запуске без переменной wildcard больше не используется по умолчанию. |
| 113 | CORS middleware возвращает 403 для чужого `Origin` до обработчика, включая preflight и WebSocket handshake через общий Router. Запрос без `Origin` допускается для CLI. Это не заменяет авторизацию токеном. |
| 114 | Тесты покрывают два origin, TTL, безопасное production-значение по умолчанию, preflight и обычный POST с чужим origin. Целевые Go-тесты прошли. |
| 115 | В Caddy для `/api/*` задан `dial_timeout 5s` и `response_header_timeout 20s`; Caddyfile прошёл `caddy validate`. Поведение медленного upstream на предельной нагрузке не измерено. |
| 116 | Добавлен `.github/workflows/docker.yml`: матрица backend/frontend, сборка по commit, Trivy с отказом на исправимых HIGH/CRITICAL, публикация SHA-тега в GHCR и дополнительного тега `vX.Y.Z` при релизном ref. YAML разобран локально; реальный GitHub Actions и push не запускались. |
| 117 | Локальный smoke через HTTPS проверил `OPTIONS` от `https://localhost` (204 и echo origin) и чужого origin (403 без разрешающего заголовка), затем прошёл остальные этапы production-репетиции. |
| 118 | Добавлен [документ безопасности](../operations/security.md): origin, фактическое хранение access/refresh в `localStorage`, WebSocket token в query string, срок действия, доступ к admin API и открытые риски. |
| 119 | Дополнена [инструкция production](../operations/production.md): GHCR, параметры сессии/proxy и порядок backup → restore check → остановка API → миграция → запуск → логи; указан порядок отката совместимого кода без `down` миграций. Команды целевого сервера не исполнялись. |
| 120 | Основной [план](plan.md) обновлён. Строка 19.4 стала частичной, остальные широкие строки сохранены частичными: внешний домен, реальный CI-публикация, длинная нагрузка и откат на предыдущий релиз остаются открытыми. |

## Проверки

```sh
docker run --rm -v "$PWD/backend:/src" -w /src golang:1.24-alpine \
  sh -c 'go test ./pkg/config ./internal/adapter/http ./internal/adapter/http/middleware -count=1'
POSTGRES_PASSWORD=example SESSION_SECRET=example BACKEND_IMAGE=backend:test \
  FRONTEND_IMAGE=frontend:test DOMAIN=localhost \
  docker compose -f docker-compose.production.yml config --quiet
docker run --rm -v "$PWD/deploy/Caddyfile:/etc/caddy/Caddyfile:ro" \
  -e DOMAIN=localhost caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile
REAL_CITY_SKIP_ROLLBACK=1 REAL_CITY_ACCEPTANCE_ARTIFACTS=/tmp/real-city-acceptance-111-120 \
  bash scripts/test-production-local.sh
```

Целевые Go-тесты, `bash -n`, `git diff --check`, Compose config, Caddy validate и разбор workflow YAML прошли. Локальная production-репетиция завершилась с кодом 0: `/tmp/real-city-acceptance-111-120/result.json` показывает `status: passed`, `last_stage: complete`, `rollback: skipped`; `stages.jsonl` фиксирует успешные build, boot, proxy, frontend, gameplay, storage_outage, backup_restore, restart и shutdown. Проверены миграции 1–53, API/WS, Redis/PostgreSQL outage, восстановление backup, рестарт и SIGTERM.

**Граница результата:** публикация образов в GHCR не подтверждена, поскольку workflow не запускался на GitHub. Откат прошлых образов не проверен, так как конкретные образы не заданы. Production TLS на внешнем домене и ручная многопользовательская браузерная приёмка остаются открытыми.
