# Real City: наблюдаемость производительности — План реализации

Пунктов плана выполнено: 42/44 (95.5%).

План развивает [аудит производительности](../performance/performance-audit.md) от 14.10.2026 и дополняет фазу 17 [общего плана](plan.md). Цель — по графикам и диагностическим данным различать задержку HTTP, медленный SQL, перегрузку пула, отставание симуляции и очередей, проблемы WebSocket и узкие места рендера карты. Численные цели из аудита пока не подтверждены нагрузочным и браузерным профилированием; пороги оповещений нужно уточнить после получения базовой линии.

Первый результат внедрения — работающий локальный контур `API → Prometheus → Grafana` с панелями HTTP и WebSocket. Затем добавляются DB, simulation, очереди и сценарии профилирования. Текущий `/metrics` содержит пользовательские HTTP-счетчики и суммы времени в миллисекундах, а также WS-счетчики; это исходная точка, но для анализа p95/p99 нужны гистограммы в секундах и корректный Prometheus exposition format.

При выборе histogram, labels и хранения dashboards опираться на [рекомендации Prometheus по гистограммам](https://prometheus.io/docs/practices/histograms/), [ограничению cardinality](https://prometheus.io/docs/practices/instrumentation/) и [документацию Grafana по provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/).

## Подход к логированию

Сохранить существующий `slog`: JSON в production, text в development. Для медленных операций писать структурированные события с постоянными полями `event`, `operation`, `duration_ms`, `result`, `request_id` там, где он доступен. Для SQL указывать логическое имя операции, а не текст запроса с параметрами. Для tick и очередей писать идентификатор подсистемы, длительность, число обработанных элементов и ошибку; ID игрока, чанка, действия, события, URL с параметрами и другие неограниченные значения оставлять в логах с учетом приватности, но не помещать в labels метрик. Метрики дают динамику и агрегаты, логи помогают найти конкретный случай; корреляция строится по времени, имени операции и `request_id`.

## Фаза 0 — Инвентаризация и базовый контур

| # | Что | Файлы | Статус |
|---|---|---|---|
| 0.1 | Зафиксировать существующий `/metrics`: счетчики HTTP по route/method/status class, суммы длительности и размера ответа, готовность | `backend/internal/adapter/http/metrics.go`, `backend/internal/adapter/http/middleware/metrics.go`, `backend/internal/adapter/http/router.go` | ✅ |
| 0.2 | Зафиксировать существующие WS-метрики соединений, подписок, отправок, fan-out и drops | `backend/internal/adapter/ws/gateway.go`, `backend/internal/adapter/http/metrics.go` | ✅ |
| 0.3 | Зафиксировать существующий `slog` и сообщения о начале/конце tick, ошибках simulation и outbox | `backend/pkg/logger/logger.go`, `backend/internal/worker/simulation/runner.go`, `backend/internal/worker/outbox_dispatcher.go` | ✅ |
| 0.4 | Зафиксировать существующий dev HUD карты с FPS, числом Pixi/Three контекстов и доступной оценкой JS heap | `frontend/src/game/renderer/renderPerformanceMetrics.ts`, `frontend/src/game/IsoMap.tsx` | ✅ |
| 0.5 | Описать матрицу «симптом → метрика → проверка»: долгий viewport, placement, tick, backlog actions/outbox, WS drops, низкий FPS; указать владельца данных и источник метрики | `docs/operations/observability.md`, `docs/performance/performance-audit.md` | ✅ |
| 0.6 | Снять исходные значения с текущего `/metrics` и согласовать имена, типы, единицы, labels, интервалы scrape и ограничение cardinality; описать переход для старых имен | `docs/operations/metrics-catalog.md`, `backend/internal/adapter/http/metrics.go` | ✅ |

---

## Фаза 1 — Prometheus и Grafana в локальном окружении

| # | Что | Файлы | Статус |
|---|---|---|---|
| 1.1 | Добавить отдельный Compose overlay с Prometheus и Grafana, закрепленными версиями образов, постоянными томами, healthchecks и без включения в обычный запуск игры | `docker-compose.observability.yml`, `Makefile` | ✅ |
| 1.2 | Настроить scrape API по имени сервиса Compose, `prometheus` self-scrape и отдельную задачу для worker при его запуске; метки `job`/`instance` должны различать процессы | `deploy/observability/prometheus/prometheus.yml`, `docker-compose.observability.yml` | ✅ |
| 1.3 | Настроить локальное хранение и retention Prometheus, базовые ограничения ресурсов; добавить persist volume для Grafana | `docker-compose.observability.yml`, `deploy/observability/prometheus/prometheus.yml` | ✅ |
| 1.4 | Подключить Prometheus как provisioned data source и автоматически загружать версионируемые dashboard JSON из репозитория | `deploy/observability/grafana/provisioning/datasources/prometheus.yml`, `deploy/observability/grafana/provisioning/dashboards/dashboards.yml`, `deploy/observability/grafana/dashboards/` | ✅ |
| 1.5 | Добавить команды запуска/остановки, проверки targets и адреса локальных интерфейсов; зафиксировать, что Grafana доступна только на loopback хоста, а `/metrics` не публикуется через внешний proxy | `Makefile`, `README.md`, `docs/operations/observability.md`, `docker-compose.observability.yml` | ✅ |

---

## Фаза 2 — Контракт метрик API, HTTP и WebSocket

| # | Что | Файлы | Статус |
|---|---|---|---|
| 2.1 | Перевести экспорт на Go Prometheus registry/client либо обеспечить эквивалентную проверяемую совместимость: `HELP`/`TYPE`, корректное экранирование labels, согласованные типы и имена; сохранить существующие WS-показатели | `backend/go.mod`, `backend/internal/adapter/http/metrics.go`, `backend/internal/adapter/http/middleware/metrics.go`, `backend/internal/adapter/ws/gateway.go` | ✅ |
| 2.2 | Добавить HTTP duration histogram в секундах с buckets для игровых запросов, счетчик ответов по стабильным route templates/status class и gauge запросов в работе; исключить сам `/metrics` из измерения или явно оговорить его учет | `backend/internal/adapter/http/middleware/metrics.go`, `backend/internal/adapter/http/router.go` | ✅ |
| 2.3 | Добавить размер ответа и выделить viewport/chunks в dashboard; сохранять route templates, не использовать raw path/query/player ID и не терять метрики при панике обработчика | `backend/internal/adapter/http/middleware/metrics.go`, `backend/internal/adapter/http/middleware/response_recorder.go` | ✅ |
| 2.4 | Добавить WS upgrade/error/reconnect-proxy indicators по доступным серверу событиям, отправку/доставку/дропы и размер fan-out; измерять очередь отправки и медленных потребителей только там, где очередь реально существует | `backend/internal/adapter/ws/gateway.go`, `backend/internal/adapter/ws/connection.go`, `backend/internal/adapter/ws/metrics.go` | ✅ |
| 2.5 | Зафиксировать ограниченный перечень labels (`operation`, `component`, `result`, `method`, `route`, `status_class`) и бюджет серий; добавить регистрацию и сбор runtime/process метрик Go отдельно для каждого процесса | `backend/internal/observability/metrics.go`, `docs/operations/metrics-catalog.md` | ✅ |

---

## Фаза 3 — Postgres и горячие операции

| # | Что | Файлы | Статус |
|---|---|---|---|
| 3.1 | Экспортировать `database/sql` pool stats (`open`, `in_use`, `idle`, `wait_count`, `wait_duration_seconds_total`, закрытия по причинам) отдельно для API и worker; учитывать два пула при расчете лимита Postgres | `backend/internal/adapter/postgres/db.go`, `backend/cmd/api/app.go`, `backend/cmd/worker/main.go` | ✅ |
| 3.2 | Ввести тонкий замер длительности и результата операций репозитория без labels по SQL/ID; определить buckets в секундах и не удваивать наблюдения при вложенных вызовах | `backend/internal/adapter/postgres/metrics.go`, `backend/internal/observability/metrics.go` | ✅ |
| 3.3 | Инструментировать world hot path: `GetOrCreateChunks`, batch `findChunks`, создание отсутствующих чанков/`COPY`, `UpdateTile`, cache hit/miss/size; разнести длительность чтения и генерации | `backend/internal/adapter/postgres/world_repo.go`, `backend/internal/adapter/postgres/metrics.go` | ✅ |
| 3.4 | Инструментировать размещение и viewport построек: `PlayerPlacementStats`, footprint intersection, viewport list, insert; отдельно измерять критическую последовательность сервиса без раскрытия координат и игрока | `backend/internal/adapter/postgres/building_repo.go`, `backend/internal/service/building.go` | ✅ |
| 3.5 | Инструментировать `ListActiveForTick`, `CountAliveBySpawn`, `FetchDue`, `MarkDone`/`MarkFailed`, outbox `FetchDue`/`MarkSent`/retry; показывать SQL ошибки по классу результата | `backend/internal/adapter/postgres/monster_repo.go`, `backend/internal/adapter/postgres/action_repo.go`, `backend/internal/adapter/postgres/outbox_repo.go` | ✅ |
| 3.6 | Подготовить runbook: по росту p95 SQL и pool wait выбирать конкретную операцию, затем снимать `EXPLAIN (ANALYZE, BUFFERS)` на тестовых данных и сопоставлять с индексами; не запускать тяжелый `EXPLAIN ANALYZE` на живой нагрузке без отдельного решения | `docs/operations/observability.md`, `docs/performance/performance-audit.md` | ✅ |

---

## Фаза 4 — Симуляция, очереди и отдельный worker

| # | Что | Файлы | Статус |
|---|---|---|---|
| 4.1 | Добавить tick duration histogram, счетчики запусков/ошибок/паник и gauge времени последнего успешного tick; отдельно учитывать scheduled tick и `CatchUp`, чтобы интерактивные вызовы не искажали периодический lag | `backend/internal/worker/simulation/runner.go`, `backend/internal/observability/simulation.go` | ✅ |
| 4.2 | Измерить длительность, processed/failed и batch saturation по ограниченному набору подсистем: actions, buildings, production, resources, monster spawning, monster AI; увидеть этап, из-за которого tick дольше интервала | `backend/internal/worker/simulation/runner.go`, `backend/internal/observability/simulation.go` | ✅ |
| 4.3 | Добавить action backlog: число due/pending, возраст oldest due в секундах, fetched/processed/retried/failed; определить легкий агрегатный запрос с индексом и интервалом сбора, чтобы сама метрика не тормозила БД | `backend/internal/adapter/postgres/queue_metrics.go`, `backend/internal/worker/simulation/runner.go`, `backend/db/migrations/000023_observability_queue_indexes.sql`, `backend/internal/observability/queues.go` | ✅ |
| 4.4 | Добавить те же признаки для outbox, плюс dead letters и длительность dispatch; разделить задержку получения из БД и публикации в EventBus | `backend/internal/adapter/postgres/queue_metrics.go`, `backend/internal/worker/outbox_dispatcher.go`, `backend/internal/observability/simulation.go` | ✅ |
| 4.5 | Отразить просрочку production/jobs и задержку завершения построек как агрегаты, если очереди действий их не охватывают; не суммировать один и тот же backlog дважды | `backend/internal/adapter/postgres/queue_metrics.go`, `backend/internal/observability/queues.go` | ✅ |
| 4.6 | Экспортировать метрики из встроенного worker через registry API; для самостоятельного `cmd/worker` поднять отдельный внутренний HTTP listener `/metrics` с собственным портом и graceful shutdown; не запускать одновременно две активные симуляции на одной БД | `backend/cmd/api/app.go`, `backend/cmd/worker/main.go`, `backend/pkg/config/config.go`, `backend/.env.example`, `backend/Dockerfile`, `docker-compose.observability.yml` | ✅ |
| 4.7 | Добавить heartbeat и выявление отсутствующего worker по `up`/времени последнего успешного tick; различать scrape failure, остановку процесса и tick, который завис или пропускается | `backend/internal/observability/simulation.go`, `deploy/observability/prometheus/alerts.yml` | ✅ |

---

## Фаза 5 — Grafana: диагностика и оповещения

| # | Что | Файлы | Статус |
|---|---|---|---|
| 5.1 | Dashboard «Обзор»: `up`, частота запросов, ошибки, p50/p95/p99 HTTP, WS connections/drops, tick duration/interval, backlog и pool saturation; переменные `job`/`instance` | `deploy/observability/grafana/dashboards/overview.json` | ✅ |
| 5.2 | Dashboard «API и карта»: route breakdown для `/world/chunks`, `/world/viewport` и placement, задержка HTTP рядом с duration горячих SQL, cache hit/miss и созданием чанков | `deploy/observability/grafana/dashboards/api-world.json` | ✅ |
| 5.3 | Dashboard «Simulation и доставка»: длительность каждого этапа, обработанные/ошибочные элементы, lag action/outbox, retries/dead letters, WS fan-out/drops; не усреднять гистограммы между instance до суммирования bucket | `deploy/observability/grafana/dashboards/simulation.json` | ✅ |
| 5.4 | Записать исходные PromQL для p95/p99, error rate, queue age и pool wait; для histogram квантилей агрегировать bucket по `le`, для счетчиков применять `rate`/`increase`, единицы показывать явно | `docs/operations/metrics-catalog.md`, `deploy/observability/grafana/dashboards/` | ✅ |
| 5.5 | Добавить правила `up == 0`, длительный tick относительно интервала, рост oldest due, ошибки обработки, рост WS drops и pool wait; настроить `for` и первичные пороги после базовой линии, указать действие и runbook для каждого правила | `deploy/observability/prometheus/alerts.yml`, `docs/operations/observability.md` | ✅ |
| 5.6 | Описать локальный просмотр алертов в Prometheus и маршрут уведомлений для staging/production при появлении рабочего канала; не закладывать чужие учетные данные в репозиторий | `docs/operations/observability.md`, `deploy/observability/prometheus/alerts.yml` | ✅ |

---

## Фаза 6 — Клиентское профилирование и сопоставление с сервером

| # | Что | Файлы | Статус |
|---|---|---|---|
| 6.1 | Расширить dev HUD: frame time p50/p95, FPS, visible tiles/buildings/resources/monsters, Pixi children и размеры retained caches, created/destroyed за redraw; сбрасывать счетчики при размонтировании карты | `frontend/src/game/renderer/renderPerformanceMetrics.ts`, `frontend/src/game/renderer/PixiStage.tsx`, `frontend/src/game/IsoMap.tsx` | ✅ |
| 6.2 | Документировать воспроизводимые desktop/mobile сценарии `?perf=buildings`, `?perf=monsters`, `?perf=mixed`: warm-up, pan/zoom, длительность, количество объектов, повторения и фиксация Chrome Performance/Memory и WebGL кадров | `frontend/src/game/dev/performanceScenarios.ts`, `docs/performance/browser-profiling.md` | ✅ |
| 6.3 | Записывать baseline FPS, frame time, heap/GC и число объектов рядом с API/DB/WS графиками для одинакового временного окна; отделять рендерную задержку от сетевой, сохранять версию сборки и параметры устройства в протоколе прогона | `docs/performance/browser-profiling.md`, `docs/performance/performance-audit.md` | ✅ (протокол; замеры — 7.4) |
| 6.4 | Если для staging нужна агрегированная клиентская телеметрия, спроектировать opt-in sampling и серверный прием без персональных данных и произвольных labels; браузер не должен напрямую отправлять значения в Prometheus | `frontend/src/shared/telemetry/`, `backend/internal/adapter/http/handler/client_performance.go`, `docs/operations/metrics-catalog.md` | ✅ (проектирование; прием отложен до потребности) |

---

## Фаза 7 — Проверка, сопровождение и документация

| # | Что | Файлы | Статус |
|---|---|---|---|
| 7.1 | Проверить валидность exposition, стабильность имен/labels, корректность histogram buckets и отсутствие персональных/неограниченных значений; тестами покрыть HTTP panic/404, пустые выборки и одновременное обновление счетчиков | `backend/internal/adapter/http/metrics_test.go`, `backend/internal/observability/metrics_test.go`, `backend/internal/adapter/ws/gateway_test.go` | ✅ |
| 7.2 | Проверить метрики на интеграционном сценарии Postgres: медленный запрос, заполненный pool, action/outbox backlog, успешный и ошибочный tick; убедиться, что измерение не меняет игровую семантику | `backend/internal/adapter/postgres/queue_metrics_test.go`, `backend/internal/worker/simulation/observability_test.go`, `backend/internal/worker/outbox_dispatcher_test.go` | ✅ |
| 7.3 | Проверить Compose конфигурацию и Prometheus targets, загрузку Grafana dashboards и запросы PromQL; CI gate на корректность конфигов и JSON, без обязательного поднятия полного игрового мира на каждом PR | `scripts/check-observability.sh`, `.github/workflows/observability.yml`, `docker-compose.observability.yml`, `deploy/observability/` | ⏳ (конфиги, PromQL, targets проверены; образ Grafana не загрузился из-за TLS) |
| 7.4 | Снять базовую линию для обычной карты и стресс-сценариев из аудита, затем оценить overhead сбора метрик и число серий; скорректировать buckets, scrape interval, retention и пороги по результатам | `docs/performance/observability-baseline.md`, `docs/performance/browser-profiling.md`, `deploy/observability/prometheus/` | ⏳ (локальный API baseline есть; browser/mobile и реалистичная игровая нагрузка остаются) |
| 7.5 | Описать запуск, доступы, сохранение данных, значения панелей, действия при типовых симптомах, обновление dashboards и ограничения текущей схемы (локальный EventBus, in-memory cache, отдельный worker) | `docs/operations/observability.md`, `README.md`, `docs/plans/plan.md` | ✅ |

## Порядок зависимостей

```
Фаза 0 (инвентаризация и контракт)
    ├── Фаза 1 (Prometheus и Grafana: первый рабочий контур)
    │       └── Фаза 5 (панели и оповещения после появления новых метрик)
    ├── Фаза 2 (API, HTTP и WebSocket)
    │       ├── Фаза 3 (Postgres и горячие операции)
    │       └── Фаза 4 (simulation, очереди, режим отдельного worker)
    └── Фаза 6 (браузерное профилирование; параллельно с фазами 2–4)
Фазы 1–6 → Фаза 7 (проверка, базовая линия, документация)
```
