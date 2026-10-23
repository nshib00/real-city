# Каталог метрик Real City

Состояние на 16.10.2026. Каталог фиксирует контракт после фазы 5 и исторический исходный срез фазы 0. Исходный срез ниже снят с `NewRouter` через `httptest` без TCP listener и без игровой нагрузки. Он **не является базовой линией производительности**. Нагрузочные значения собираются в фазе 7.

## Исходный `/metrics` до фазы 2

Источник: `backend/internal/adapter/http/metrics.go`, `middleware/metrics.go`, `ws/gateway.go`. Счетчики HTTP существуют только после первого запроса для сочетания labels. `/metrics` учитывает собственные вызовы, а `real_city_http_ready` всегда равен `1` при ответе обработчика и не проверяет Postgres/worker.

| Имя | Тип по смыслу | Единица | Labels | Смысл и ограничение |
|---|---|---|---|---|
| `real_city_http_ready` | gauge | 1/0 | нет | Сейчас константа `1`; не равна готовности зависимостей. |
| `real_city_http_requests_total` | counter | запросы | `method`, `route`, `status_class` | Общее число HTTP ответов. Текущий `route` фактически `unmatched` в проверенном сценарии. |
| `real_city_http_request_duration_ms_sum` | counter | миллисекунды | те же | Сумма целых миллисекунд: каждый запрос короче 1 ms добавляет `0`; percentiles недоступны. |
| `real_city_http_response_bytes_sum` | counter | байты | те же | Сумма байтов тела ответа. |
| `real_city_ws_connections` | gauge | соединения | нет | Текущие WS подключения. |
| `real_city_ws_chunk_subscriptions` | gauge | подписки | нет | Число подписок на чанки среди подключений. |
| `real_city_ws_private_subscriptions` | gauge | подписки | нет | Число приватных подписок. |
| `real_city_ws_alliance_subscriptions` | gauge | подписки | нет | Число подписок на союзный канал. |
| `real_city_ws_events_sent_total` | counter | события | нет | События, полученные gateway из EventBus; это не число доставленных сообщений. |
| `real_city_ws_fanout_total` | counter | получатели | нет | Сумма выбранных получателей для событий до постановки в очередь. |
| `real_city_ws_messages_dropped_total` | counter | сообщения | нет | Не удалось поставить сообщение в очередь соединения. |

До фазы 2 экспорт выставлял `Content-Type: text/plain; version=0.0.4` и строки образцов, но не `HELP`/`TYPE`. После фазы 2 текстовый exporter добавляет описания семейств, экранирование labels, histogram и runtime/process ряды.

## Исходный срез

В одном чистом процессе были последовательно выполнены `GET /metrics`, `GET /health`, `GET /metrics`. Первый ответ содержал `real_city_http_ready 1` и семь WS рядов со значением `0`; HTTP рядов еще не было. Второй ответ показал:

```text
real_city_http_ready 1
real_city_http_requests_total{method="GET",route="unmatched",status_class="2xx"} 2
real_city_http_request_duration_ms_sum{method="GET",route="unmatched",status_class="2xx"} 0
real_city_http_response_bytes_sum{method="GET",route="unmatched",status_class="2xx"} 305
real_city_ws_connections 0
real_city_ws_chunk_subscriptions 0
real_city_ws_private_subscriptions 0
real_city_ws_alliance_subscriptions 0
real_city_ws_events_sent_total 0
real_city_ws_fanout_total 0
real_city_ws_messages_dropped_total 0
```

Значения `2`, `0 ms` и `305 bytes` зависят от этого синтетического сценария и порядка вызовов. `route="unmatched"` для `/health` является обнаруженным дефектом разбивки по маршрутам, а не названием игрового endpoint.

## Действующий контракт после фазы 2

| Семейство | Тип и единица | Разрешенные labels | Источник |
|---|---|---|---|
| `real_city_http_requests_total` | counter, запросы | `method`, `route`, `status_class` | HTTP middleware; `route` — шаблон ServeMux либо фиксированный `unmatched` для 404. |
| `real_city_http_request_duration_seconds` | histogram, секунды | те же + `le` у bucket | HTTP middleware; p50/p95/p99 считаются по buckets после суммирования по instance. |
| `real_city_http_requests_in_flight` | gauge, запросы | без route либо только `method` | HTTP middleware. |
| `real_city_http_response_bytes_total` | counter, байты | `method`, `route`, `status_class` | HTTP middleware. |
| `real_city_ws_upgrades_total` | counter, попытки | `result`: `ok`, `auth_error`, `handshake_error`, `transport_error` | Попытки установки WS; скорость успешных upgrade служит косвенным сигналом переподключений, но не различает их с новыми клиентами. |
| `real_city_ws_messages_enqueued_total`, `real_city_ws_messages_delivered_total`, `real_city_ws_write_errors_total`, `real_city_ws_slow_consumers_total` | counters, сообщения/соединения | нет | Постановка в реальную очередь, успешная запись фрейма в сокет, ошибки записи и закрытия из-за полной очереди. Успешная запись не гарантирует обработку браузером. |
| `real_city_ws_fanout_size` | histogram, получатели на событие | только `le` у bucket | Размер выбранной аудитории; старые `real_city_ws_events_sent_total` и `real_city_ws_fanout_total` сохранены. |
| `real_city_ws_send_queue_depth`, `real_city_ws_send_queue_capacity` | gauges, сообщения | нет | Сумма длины и емкости очередей активных соединений. |
| `real_city_go_goroutines`, `real_city_go_heap_alloc_bytes`, `real_city_go_heap_inuse_bytes`, `real_city_go_gc_cycles_total`, `real_city_process_start_time_seconds` | gauges/counter, см. суффиксы | нет | Снимок Go runtime и времени старта конкретного процесса; есть у API и самостоятельного worker. |
| `real_city_db_operation_duration_seconds` | histogram, секунды | `operation`, `result`, `le` у bucket | Именованные операции Postgres репозиториев; длительность включает ожидание соединения и чтение строк. |
| `real_city_db_pool_{open,in_use,idle,max_open}_connections`, `real_city_db_pool_wait_count_total`, `real_city_db_pool_wait_duration_seconds_total`, `real_city_db_pool_{max_idle,max_idle_time,max_lifetime}_closed_total` | gauges/counters, соединения и секунды | нет | Снимок `database/sql.DBStats` пула текущего процесса. Без Postgres семейства не содержат образцов. |
| `real_city_world_operation_duration_seconds` | histogram, секунды | `operation`, `result`, `le` | Полные операции получения/создания чанков и CPU-генерация. Вложенные ряды нельзя суммировать как общий трафик. |
| `real_city_world_cache_lookups_total`, `real_city_world_cache_entries`, `real_city_world_chunks_created_total` | counter/gauge, обращения и чанки | `result=hit/miss` только у lookups | Кэш `WorldRepo` и действительно созданные в БД чанки. |
| `real_city_building_placement_duration_seconds` | histogram, секунды | `component`, `result`, `le` | `total` — весь вызов `Place`, `critical` — участок от статистики владельца до вставки и публикации. Компоненты не суммируют. |
| `real_city_simulation_tick_duration_seconds` и задержка очередей | histogram/gauge, секунды | `component`, `result` | Simulation/outbox worker. |
| Go runtime и process start | gauges/counters по смыслу, байты/горутины/Unix seconds | без пользовательских labels | Каждый процесс отдельно. |

Новые HTTP buckets: 5, 10, 25, 50, 100, 250, 500 ms и 1, 2.5, 5 s, плюс `+Inf`. `/metrics` и `/api/v1/realtime` не входят в HTTP счетчики: WebSocket измеряется отдельными рядами, а длительное соединение не искажает HTTP latency. Gauge запросов в работе не имеет labels. `route` берется у `ServeMux` до вызова цепочки middleware, включая ответы после паники, которую обрабатывает recoverer. Размер ответа измеряется по записанному телу. Dashboard «Сбор метрик» отдельно показывает p95 и частоту `/world/chunks` и `/world/viewport`.

DB, world и placement histogram используют buckets 1, 2.5, 5, 10, 25, 50, 100, 250, 500 ms, 1, 2.5 и 5 s, плюс `+Inf`. `result` ограничен `ok`, `timeout`, `not_found`, `conflict`, `error`. Для DB доступен фиксированный набор операций: `world.find_chunk`, `world.find_chunks`, `world.copy_tiles`, `world.update_tile`, `building.player_placement_stats`, `building.footprint_intersection`, `building.viewport_list`, `building.insert`, `monster.list_active_for_tick`, `monster.count_alive_by_spawn`, `action.fetch_due`, `action.mark_done`, `action.mark_failed`, `outbox.fetch_due`, `outbox.mark_sent`, `outbox.mark_failed`, `outbox.mark_dead`. World операции: `world.get_or_create_chunk`, `world.get_or_create_chunks`, `world.create_chunk`, `world.generate_chunk`. Репозиторные и сервисные длительности могут описывать вложенные этапы одного запроса, поэтому их частоты не складывают и не считают независимыми запросами.

API публикует DBStats своего пула через `/metrics`. Самостоятельный worker публикует DBStats **своего** пула через `WORKER_METRICS_ADDR` (по умолчанию `127.0.0.1:9091`); для scrape из другого контейнера адрес нужно переопределить на `:9091` внутри закрытой сети Compose. В режиме встроенного worker отдельного пула нет. Лимит каждого пула — 20 открытых соединений, 10 idle; при одновременном запуске API и самостоятельного worker планировать до 40 соединений плюс административные подключения. Одновременно активировать две симуляции на одной БД нельзя.

## Labels и cardinality

### Симуляция и очереди (фаза 4)

| Метрика | Тип | Labels | Интерпретация |
|---|---|---|---|
| `real_city_simulation_enabled` | gauge | нет | `1`, если процесс запускает встроенный или самостоятельный scheduled runner. |
| `real_city_simulation_tick_duration_seconds` | histogram | `mode`, `result` | Время tick, включая `CatchUp`; `mode=scheduled|catch_up`, `result=ok|error|panic`. |
| `real_city_simulation_ticks_total` | counter | `mode`, `result` | Запуски, ошибки и восстановленные паники; tick с ошибками отдельных действий имеет `result=error`. |
| `real_city_simulation_last_success_timestamp_seconds` | gauge | `mode` | Последний tick без ошибок, Unix seconds; `0` до первого успеха. |
| `real_city_simulation_heartbeat_timestamp_seconds` | gauge | нет | Время окончания последнего scheduled tick независимо от результата; `0` до первого окончания. |
| `real_city_simulation_stage_duration_seconds` | histogram | `component`, `result` | Этапы **только scheduled**: `actions`, `buildings`, `production`, `resources`, `monster_spawning`, `monster_ai`. |
| `real_city_simulation_stage_items_total` | counter | `component`, `result` | `processed` — возвращенное число элементов, `failed` — ошибки обработки элементов и этапа. |
| `real_city_simulation_stage_saturated_total` | counter | `component` | Этап вернул не меньше batch limit; для spawning/AI показатель приблизительный. |
| `real_city_action_items_total` | counter | `result` | `fetched`, `processed` (подтверждено), `retried` (повтор запланирован), `failed` (не удалось сохранить статус). |
| `real_city_outbox_dispatch_duration_seconds` | histogram | `component`, `result` | Раздельно `fetch`, `publish`, `total`; результаты из фиксированного словаря. `publish` измеряет синхронный вызов EventBus. |
| `real_city_outbox_items_total` | counter | `result` | `fetched`, `sent`, `retried`, `dead`, `failed`. |
| `real_city_queue_pending`, `real_city_queue_due`, `real_city_queue_oldest_due_age_seconds` | gauge | `component` | Агрегаты из Postgres: `actions`, `outbox`, `buildings`, `production`; `due` включает уже захваченные/заблокированные элементы. |
| `real_city_queue_dead` | gauge | нет | Мертвые письма outbox. |
| `real_city_queue_snapshot_timestamp_seconds` | gauge | нет | Время последнего **полного успешного** сбора очередей; при ошибке значения остаются прежними. |

Очереди читаются раз в 30 секунд, суммарный timeout чтения 3 секунды. `pending` включает задачи с будущим сроком; `oldest_due_age_seconds=0`, когда просроченных задач нет. Источники `buildings` и `production` показывают состояние доменных таблиц, которое частично пересекается с заданиями в `actions`: **не складывать четыре очереди** как независимые задачи. Новые индексы в миграции `000022` уменьшают стоимость сбора; счетчики pending и dead все равно обходят подходящие записи индекса, поэтому стоимость оценивают по объему и `EXPLAIN` на тестовой базе. У всех histogram длительность в секундах и те же buckets, что у DB metrics.

Для отсутствующей БД gauges очередей не публикуются. Ошибочный запрос оставляет предыдущий снимок, поэтому контролировать `time() - real_city_queue_snapshot_timestamp_seconds`.

## PromQL для диагностики (фаза 5)

В Grafana доступны dashboards «Обзор производительности», «API и карта», «Simulation и доставка». Для графиков используется окно `[5m]` при scrape раз в 15 секунд. При малом числе наблюдений квантиль гистограммы нестабилен; пустой ряд означает отсутствие соответствующих вызовов, а не нулевую задержку. При выборе нескольких instance сначала суммируются bucket по `le` и нужной размерности, затем вычисляется квантиль. Средние p95 по instance математически неверны.

```promql
# HTTP p95 по шаблону маршрута; для p99 заменить 0.95 на 0.99.
histogram_quantile(0.95, sum by (le, route) (rate(real_city_http_request_duration_seconds_bucket{job="api"}[5m])))

# Доля 5xx среди HTTP ответов, 0..1. 4xx не считаются ошибкой сервера.
sum(rate(real_city_http_requests_total{job="api",status_class="5xx"}[5m]))
/
clamp_min(sum(rate(real_city_http_requests_total{job="api"}[5m])), 0.000001)

# DB p95 для горячих операций. При фильтрации нескольких instance bucket сначала суммируются.
histogram_quantile(0.95, sum by (le, operation) (rate(real_city_db_operation_duration_seconds_bucket{operation=~"world\\..*|building\\..*"}[5m])))

# Возраст самой старой просроченной записи в actions и outbox, секунды.
real_city_queue_oldest_due_age_seconds{component=~"actions|outbox"}

# Счетчик обработанных ошибок за 5 минут; пригоден для редких событий.
sum by (component) (increase(real_city_simulation_stage_items_total{result="failed"}[5m]))

# Среднее ожидание свободного соединения среди ожидавших запросов, секунды.
rate(real_city_db_pool_wait_duration_seconds_total[5m])
/
rate(real_city_db_pool_wait_count_total[5m])
```

Для pool wait при нуле ожидавших запросов ряд отсутствует; панель «Обзор» использует `clamp_min` для устойчивого отображения нуля, а правило оповещения дополнительно требует более пяти ожиданий за пять минут. `rate` применяют к счетчикам для графика скорости, `increase` — к числу редких событий за окно. Gauge очереди читают напрямую: `rate` для него не нужен. Единицы в панелях указаны как `s`, запросы/секунду, события/секунду, число элементов или доля `0..1`.

- Разрешены только имена `method`, `route`, `status_class`, `operation`, `component`, `mode`, `result` и служебное `le`. Значения должны быть из конечных списков. Для WS причины отказа задаются кодами из небольшого словаря, а не текстом ошибки.
- Запрещены ID игрока/соединения/чанка/действия, координаты, SQL текст/параметры, raw path/query, IP, user agent, `request_id`. Их место — защищенные структурированные логи при необходимости.
- Начальный бюджет: до 5 000 активных рядов на API instance и до 1 000 на worker instance после добавления всех histogram buckets. На приемке измерить фактическое число; семейство с потенциально более чем 100 вариантами labels пересмотреть до развертывания. Для route использовать зарегистрированные шаблоны, не URL с ID.
- Не вводить labels для пустого значения произвольной строки. Результаты операций группировать как `ok`, `timeout`, `not_found`, `conflict`, `error`; только у cache lookups `result` принимает `hit` или `miss`.

## Сбор и переход имен

Клиентские показатели сейчас локальны для dev HUD и Chrome trace; Prometheus их не собирает. Возможный staging-прием описан в [протоколе браузерного профилирования](../performance/browser-profiling.md): только opt-in, ограниченная выборка и частота, конечные категории на сервере, без персональных данных и произвольных labels. До утверждения retention и доступа endpoint и метрики для него не создаются.

Начальная конфигурация для локального контура: scrape API раз в 15 s, отдельного worker — тоже раз в 15 s при его запуске. Таймаут 5 s, чтобы scrape не висел дольше интервала. Это начальные настройки, которые корректируются по стоимости сбора и нужной точности после baseline. API и отдельный worker получают разные `job`/`instance`; при встроенном worker его ряды принадлежат API процессу. Не объединять счетчики двух активных симуляций на одной БД.

Переход выполнен: сохранены `real_city_http_requests_total` и прежние `real_city_ws_*`; новая histogram в секундах публикуется рядом со старой `real_city_http_request_duration_ms_sum`, а `real_city_http_response_bytes_total` — рядом со старой `_sum`. Устаревшие ряды удалить отдельным изменением после перевода dashboards. `real_city_http_ready` — только совместимый индикатор обработчика; для доступности использовать `up`.
