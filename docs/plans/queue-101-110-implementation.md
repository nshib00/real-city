# Очередь 101–110: фактический результат

Дата: 01.11.2026. [Постановка](queue-101-110.md). Изменения и проверки выполнены на текущем рабочем дереве. Production-репетиция использует отдельный Compose-проект и удаляет свои тома; рабочий тестовый мир не очищался.

| № | Результат |
| --- | --- |
| 101 | `/ready` ограничен одной секундой на ping и одним одновременно зависшим вызовом драйвера. Если драйвер игнорирует отмену контекста, HTTP всё равно получает 503; после возврата драйвера слот освобождается. Игровые SQL-запросы этой правкой не менялись. |
| 102 | Добавлены тесты для драйвера, игнорирующего отмену, быстрого повторного отказа без второго ping, восстановления, ошибки ping и режима без БД; проверен также HTTP `/ready` без DBPool. Целевой Go-тест прошёл в контейнере Go 1.24.13. |
| 103 | В локальном production Compose HTTP-запрос на порт 80 перенаправился на `https://localhost` с сохранением пути. |
| 104 | Проверены `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`. Обнаружен и исправлен реальный дефект: `/metrics` обслуживался SPA fallback с кодом 200, несмотря на правило `respond`. Теперь `/metrics` и `/debug/pprof` получают 404 через отдельный `handle`. |
| 105 | Большой JSON-запрос через Caddy получил HTTP 413; лимит тела `/api/*` остался 1 МБ. Запрос может начать передаваться backend до отказа, поэтому проверка утверждает результат для клиента, а не отсутствие любого upstream-трафика. |
| 106 | В production Compose проброшены HTTP/WS-таймауты, размеры пула PostgreSQL и параметры симуляции с исходными значениями по умолчанию; дополнен `.env.prod.example`. `docker compose config --quiet` прошёл. |
| 107 | В одноразовом Compose API получил SIGTERM через `docker compose stop -t 15`; код выхода контейнера 0. API затем запущен снова, `/ready` вернул 200. Это проверка штатного выхода процесса, не всех незавершённых игровых операций. |
| 108 | Новые проверки встроены в `scripts/test-production-local.sh`. Скрипт останавливается на ошибке, пишет `result.json` и `stages.jsonl`; пропущенный откат отмечается `skipped`. Синтаксис shell проверен. |
| 109 | Обновлена [инструкция production](../operations/production.md): новые проверки, бюджет `/ready`, параметры runtime и границы приёмки. |
| 110 | Основной [план](plan.md) обновлён по проверенному объёму. Широкие строки 18.4–18.8 и 26.5 оставлены частичными: внешний стенд, proxy timeout limits, политика токенов и настоящий откат не проверены. |

## Команды и свидетельства

```sh
docker run --rm -v "$PWD/backend:/src" -w /src golang:1.24-alpine \
  sh -c 'go test ./internal/adapter/http -run "TestReadinessProbe|TestRouterMiddlewareSmoke" -count=1'

POSTGRES_PASSWORD=example SESSION_SECRET=example \
  BACKEND_IMAGE=backend:test FRONTEND_IMAGE=frontend:test DOMAIN=localhost \
  docker compose -f docker-compose.production.yml config --quiet

REAL_CITY_SKIP_ROLLBACK=1 \
  REAL_CITY_ACCEPTANCE_ARTIFACTS=/tmp/real-city-acceptance-101-110-verified \
  bash scripts/test-production-local.sh
```

Первый прогон завершился на проверке `/metrics` и обнаружил доступность SPA по этому пути. Второй прогон после исправления маршрута дошёл до проверки тела и показал, что некорректный запрос формы получает 400 от backend, не проверяя лимит Caddy. Третий прогон с большим JSON прошёл весь сценарий: HTTPS/proxy, игровой API/WS, сбои PostgreSQL/Redis, восстановление backup, рестарт и SIGTERM. После него исправлена маркировка пропущенного отката в `stages.jsonl` и добавлен численный порог 1,5 секунды для `/ready`. Следующий прогон выявил гонку в `verify-production-backup.sh`: `pg_isready` видел временный Unix-сервер инициализации контейнера, который закрывался до `createdb`. Ожидание и restore переключены на финальный TCP-сервер; репетиция повторена.

Финальный прогон завершился с кодом 0. `/tmp/real-city-acceptance-101-110-complete/result.json` содержит `passed`, этап `complete`, `rollback: skipped`; `stages.jsonl` помечает build, boot, proxy, frontend, gameplay, storage_outage, backup_restore, restart и shutdown как `passed`, rollback как `skipped`. `bash -n` для обоих изменённых shell-скриптов, `git diff --check` и `docker compose config --quiet` также прошли.

Откат на старые образы был явно пропущен (`REAL_CITY_SKIP_ROLLBACK=1`), поскольку конкретные образы предыдущего релиза не заданы. Проверка публичного домена и сертификата, целевого сервера, долгой нагрузки, полного браузерного пути и устойчивости каждого игрового SQL-действия к зависшей БД остаётся открытой.
