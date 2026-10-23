# Наблюдаемость производительности Real City

Этот документ связывает симптомы из [аудита производительности](../performance/performance-audit.md) с измерениями и первыми действиями при диагностике. Текущий состав метрик, единицы и исходный срез приведены в [каталоге метрик](metrics-catalog.md). Этапы развития контура указаны в [плане наблюдаемости](../plans/observability-plan.md).

## Локальный запуск Prometheus и Grafana

Из корня репозитория выполнить `make observability-up`. Команда запускает Postgres и Redis, применяет миграции, затем поднимает API, Prometheus и Grafana из отдельного `docker-compose.observability.yml`. Обычные `make backend-up` и `docker compose up` не запускают сервисы наблюдаемости. Для остановки только Prometheus и Grafana служит `make observability-down`; данные остаются в `prometheus_data` и `grafana_data`. `make observability-logs` показывает логи обоих сервисов.

Адреса с машины, на которой запущен Compose:

| Интерфейс | Адрес | Назначение |
|---|---|---|
| Prometheus targets | <http://127.0.0.1:9090/targets> | Проверка `prometheus` и `api`: состояние `UP`, последний scrape и ошибки. |
| Prometheus query | <http://127.0.0.1:9090/graph> | Запросы `up`, `real_city_http_ready`, `real_city_ws_connections`. |
| Prometheus alerts | <http://127.0.0.1:9090/alerts> | Состояния правил: inactive, pending, firing; ошибки загрузки правил — в логах Prometheus. |
| Grafana | <http://127.0.0.1:3000/> | Папка `Real City`: «Сбор метрик», «Обзор производительности», «API и карта», «Simulation и доставка». |

Первый вход в Grafana — `admin` / `admin`. Для другой локальной учетной записи перед запуском установить `GRAFANA_ADMIN_USER` и `GRAFANA_ADMIN_PASSWORD` в окружении. При уже созданном volume изменение этих переменных не сбрасывает существующий пароль. Порты Prometheus и Grafana привязаны к loopback хоста. Prometheus получает `/metrics` API внутри сети Compose по `backend:8080`; Grafana обращается к `prometheus:9090`. Текущий dev Compose отдельно публикует API на порту 8080 всех интерфейсов, поэтому `/metrics` доступен и через этот порт. Для доступа только с локальной машины нужно ограничить публикацию API или входящий трафик. Не направлять публичный игровой proxy на `/metrics` и не публиковать порт самостоятельного worker наружу.

`make observability-targets` выводит активные цели через API Prometheus. `job=api, instance=backend:8080` относится к процессу API со встроенной симуляцией, а `job=prometheus, instance=prometheus:9090` — к самому сборщику. Самостоятельный `cmd/worker` экспортирует `/metrics` на `WORKER_METRICS_ADDR` (по умолчанию `127.0.0.1:9091`). Файл `deploy/observability/prometheus/worker-targets.yml` пока содержит `[]`, потому что локальный Compose не запускает отдельный worker. При запуске worker в той же сети Compose задайте `WORKER_METRICS_ADDR=:9091` внутри контейнера и укажите `- targets: ["worker:9091"]`; Prometheus обнаружит изменение без перезапуска. Не публикуйте порт worker наружу. Не запускать одновременно самостоятельный worker и встроенную симуляцию API на одной БД.

Prometheus собирает цели каждые 15 секунд с timeout 5 секунд и хранит локальные данные до 7 суток или 2 GB, в зависимости от того, какой предел достигнут раньше. Для каждого сервиса задан лимит памяти 512 MiB и 1 CPU. Dashboard «Обзор производительности» связывает HTTP, WebSocket, tick, очереди и Postgres pool. «API и карта» показывает маршруты рядом с DB/world/cache, а «Simulation и доставка» — этапы, очереди и fan-out. Откройте одинаковое временное окно на связанных панелях; пустые серии при отсутствии запросов или отключенном worker ожидаемы.

## Границы текущего состояния

- API экспортирует `/metrics` в текстовом формате Prometheus с `HELP`/`TYPE`: HTTP, WS, Go runtime, DB pool, именованные операции Postgres, cache, размещение, tick и очереди. Самостоятельный worker экспортирует собственные DB pool/operation, runtime, tick и очереди. Агрегированная клиентская телеметрия пока не экспортируется.
- В коде есть `slog` для HTTP, simulation и outbox. Логи помогают найти конкретный случай по времени и операции рядом с временными рядами метрик.
- В dev HUD карты доступны FPS, p50/p95 интервала кадров, число видимых объектов, Pixi children, размеры retained caches, churn за redraw, число Pixi contexts/Three previews и JS heap там, где браузер открывает `performance.memory`. Протокол измерений приведен в [профилировании браузера](../performance/browser-profiling.md).
- API запускает simulation и outbox внутри собственного процесса. Существует также отдельный `cmd/worker`; при диагностике сначала уточнить режим запуска, чтобы не принять метрики API за метрики самостоятельного worker.
- Исторический исходный срез фазы 0 имел `route="unmatched"` даже для `/health`. После фазы 2 route берется у `ServeMux`; `unmatched` остается для неизвестных маршрутов.

## Диагностика scheduled tick и очередей

В API по умолчанию работает встроенный scheduled runner: его метрики находятся в `job=api`. `CatchUp` получает `mode="catch_up"`, а метрики этапов содержат только scheduled tick. Сначала сравните `histogram_quantile(0.95, sum by (le, component) (rate(real_city_simulation_stage_duration_seconds_bucket{result="ok"}[5m])))` с интервалом `SIMULATION_TICK_INTERVAL`. Если этап достигает размера пачки, смотрите `rate(real_city_simulation_stage_saturated_total[5m])`, затем возраст просрочки `real_city_queue_oldest_due_age_seconds` и `real_city_queue_due` для того же component. Для tick в целом используйте `histogram_quantile(0.95, sum by (le, mode) (rate(real_city_simulation_tick_duration_seconds_bucket[5m])))`; эти длительности включают вложенные этапы и не складываются с ними.

База снимает снимок очередей каждые 30 секунд отдельным фоновым циклом, с общим timeout 3 секунды; `/metrics` только читает уже готовые значения. Если `time() - real_city_queue_snapshot_timestamp_seconds > 120`, исследуйте Postgres и логи `observability.queues.failed` прежде, чем интерпретировать backlog. `pending` включает будущие задания, `due` включает захваченные записи, а возраст равен нулю без просрочки. `buildings`/`production` измеряют доменные таблицы и могут отражать те же задания, что и `actions`; не суммируйте их. Для outbox разбивка `real_city_outbox_dispatch_duration_seconds{component="fetch|publish|total"}` позволяет сравнить получение из БД и публикацию в локальный EventBus; успешная публикация в память сама по себе не подтверждает доставку по WebSocket.

Правила `deploy/observability/prometheus/alerts.yml` различают: `up == 0` — target не скрейпится; свежий scrape при старом heartbeat — scheduled tick не завершился; свежий heartbeat при старом успешном tick — цикл выполняется с ошибками. Отсутствие настроенного target в `worker-targets.yml` не порождает `up{job="worker"}` и не означает остановку worker: для alert о его исчезновении цель должна оставаться в конфигурации обнаружения.

## Оповещения и первичные действия

Локальные правила просматриваются по адресу <http://127.0.0.1:9090/alerts>, список и состояние группы — на <http://127.0.0.1:9090/rules>. При `pending` Prometheus уже видит условие, но выдерживает `for`; `firing` означает, что оно держится всё заданное время. Сначала проверить `up` и свежесть снимка очередей, затем открыть соответствующий dashboard на том же временном окне. Правила только локально отображаются в Prometheus: маршрута внешних уведомлений пока нет.

Пороги пока стартовые: tick p95 > 1 s при `SIMULATION_TICK_INTERVAL=1s`, oldest due > 60 s и рост более чем на 30 s за 10 минут, WS drops > 5 за 5 минут, среднее pool wait > 50 ms при более чем пяти ожиданиях за 5 минут. Для редких ошибок этапов/actions/outbox порог — хотя бы одно событие за 5 минут. `for` составляет 1–5 минут в зависимости от правила. После базовой линии фазы 7 записать нормальные p95, объем трафика, длину очередей и частоту фоновых ошибок; затем изменить численные пороги и `for` под staging/production. Если интервал tick изменится, обновить правило `RealCitySimulationTickSlow` и линии 1 s в dashboards. Числа из этого раздела не являются подтвержденными SLA.

### Недоступен scrape

`RealCityScrapeUnavailable`: открыть `/targets` и ошибку последнего scrape, проверить процесс API/worker, `/metrics` и сеть Compose. Если worker намеренно выключен, удалить его target из `worker-targets.yml`; если должен работать — оставить target и восстановить процесс. Проверить, не превышает ли сбор 5 s timeout.

### Tick не завершается или длится дольше интервала

`RealCitySimulationHeartbeatMissing`, `RealCitySimulationNoSuccess`, `RealCitySimulationTickSlow`: сравнить `up`, возраст heartbeat, возраст последнего успеха и p95 scheduled tick в «Simulation и доставка». Если heartbeat старый, искать зависший этап и ожидание БД. Если heartbeat свежий, а успех старый — смотреть `real_city_simulation_stage_items_total{result="failed"}` и логи `simulation.tick.finish`. При p95 > 1 s сравнить этапы, batch saturation и pool wait; `CatchUp` не учитывается в этом правиле.

### Растет возраст очереди

`RealCityQueueAgeGrowing` и `RealCityQueueSnapshotStale`: сперва проверить свежесть снимка `time() - real_city_queue_snapshot_timestamp_seconds`; при старом снимке проверить Postgres и `observability.queues.failed`. Затем открыть due, age и throughput для конкретного `component`; у actions проверить batch saturation и ошибки обработки, у outbox — fetch/publish и dead letters. `buildings` и `production` могут пересекаться с `actions`; значения не суммировать.

### Ошибки обработки и доставки

`RealCitySimulationStageErrors`, `RealCityActionProcessingErrors`, `RealCityOutboxProcessingErrors`: выбрать `component`/`result`, сопоставить прирост счетчиков с логами и p95 DB операции. `action_items{result="failed"}` означает ошибку сохранения статуса; ошибки отдельного action также видны в счетчике этапа. Для outbox `dead` означает исчерпание попыток; проверить payload и причину по защищенным логам, затем решить о повторной отправке после устранения причины.

### Потери WebSocket

`RealCityWebSocketDrops`: открыть «Simulation и доставка», сравнить drops с fan-out, глубиной send queue, slow consumers и write errors. Проверить медленные соединения и доставку из локального EventBus. В режиме самостоятельного worker EventBus не передает события в API процесс, поэтому эти метрики не подтверждают межпроцессную доставку.

### Ожидание пула Postgres

`RealCityDatabasePoolWait`: сопоставить долю занятых соединений с ожиданием и p95 именованных операций. В API и самостоятельном worker пулы раздельные; выбрать нужный `job`/`instance`. Найти занявшую пул операцию, проверить SQL/план на тестовой базе и только затем решать вопрос лимитов соединений.

### Маршрут уведомлений для staging и production

До появления рабочего канала дежурный просматривает `/alerts` вручную. Когда будет согласован канал, подключить Alertmanager или Grafana contact point вне локального Compose, направить `severity=warning` соответствующей команде и добавить группировку по `alertname`, `job`, `instance`; подавлять повторные уведомления по принятой политике дежурства. URL webhook, токены, адреса получателей и секреты хранить в секретах окружения развертывания, не в репозитории. Проверить тестовым правилом путь от `firing` до получения уведомления до включения в production. В текущем репозитории внешний receiver не настроен и никакие уведомления не отправляются.

Самостоятельный worker имеет внутренний `/metrics` на `WORKER_METRICS_ADDR`. Для варианта Compose задайте `SIMULATION_EMBEDDED=false` **до** запуска API и worker, затем выполните `SIMULATION_EMBEDDED=false docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.observability.yml --profile standalone-worker up -d --build backend worker prometheus grafana`. Overlay передает этот флаг API и worker, а `WORKER_METRICS_ADDR=:9091` доступен только внутри сети; worker дополнительно проверяет флаг перед запуском. Замените содержимое `deploy/observability/prometheus/worker-targets.yml` на `- targets: ["worker:9091"]`: Prometheus подхватит изменение файла. Возврат к встроенной симуляции: остановить отдельный worker, вернуть в targets `[]` и запустить API снова с `SIMULATION_EMBEDDED=true`. Не запускайте две симуляции на одной БД: у monster AI нет распределенного claim. Важно: EventBus в текущем проекте локален процессу. При самостоятельном worker outbox публикует события только в своем процессе; до появления межпроцессной доставки игровой WebSocket API не получает эти события. Для полноценной игры оставьте встроенный режим.


## Матрица диагностики

«Владелец» ниже означает компонент, который производит данные. `Сейчас` указывает доступный сигнал, `Далее` — метрику, которую добавят следующие фазы плана.

| Симптом | Владелец и источник | Сейчас | Далее | Первая проверка |
|---|---|---|---|---|
| Медленно открывается viewport или чанки карты | API HTTP middleware; `WorldRepo.GetOrCreateChunks` и `findChunks` | HTTP p95, `world.get_or_create_chunks`, `world.find_chunks`, `world.generate_chunk`, `world.copy_tiles`, cache hit/miss и число созданных чанков | Панели API/карта в фазе 5 | Сопоставить HTTP и операции world/DB. Рост `create_chunk` или `copy_tiles` указывает на создание; рост `find_chunks` — на чтение. |
| Долго размещается здание | API HTTP middleware; `BuildingService`, `BuildingRepo` | HTTP p95, `building_placement_duration_seconds` по `total`/`critical`, DB p95 для stats, footprint и insert; лог с `request_id` | Панели API/карта в фазе 5 | Сопоставить HTTP и этапы размещения. При росте pool wait сначала проверить пул. |
| Tick идет дольше интервала или пропускается | Встроенный API worker либо `cmd/worker`; `simulation.Runner` | `simulation.tick.finish` и `simulation_tick_duration_seconds`, `simulation_last_success_timestamp_seconds`, heartbeat, stage histogram/counts | Панель simulation в фазе 5 и baseline в фазе 7 | Сравнить duration с `SIMULATION_TICK_INTERVAL`, проверить ошибки и подсистему с самым долгим этапом. Затем проверить DB pool/SQL. |
| Растет задержка actions | `simulation.Runner`, `ActionRepo` | `simulation.action.done/failed`, `queue_due`/`queue_oldest_due_age_seconds`, `action_items_total`, saturation | Панель simulation в фазе 5 | Проверить, успевает ли batch обработать due actions, ошибки и длительность `FetchDue`/`MarkDone`. |
| Растет задержка outbox и обновления приходят поздно | `OutboxDispatcher`, `OutboxRepo`, `EventBus` | `outbox.dispatch.sent/failed/dead`, `queue_dead`/`queue_due`, `outbox_dispatch_duration_seconds` | Панель simulation в фазе 5 | Сравнить время ожидания в outbox с длительностью публикации и WS fan-out; отдельно проверить DB ошибки и retries. |
| WS события теряются или доставляются не всем | `ws.Gateway`, `Connection` | `real_city_ws_*`: connections, subscriptions, events, fanout histogram, drops, upgrades, send queue, slow consumers и write errors | Клиентская телеметрия переподключений при необходимости | Сравнить drops с fanout и количеством соединений; проверить `ws.message_dropped`, заполнение send queue и отказы upgrade. Reconnect браузера сервер напрямую не измеряет. |
| Карта тормозит при pan/zoom или множестве объектов | `PixiStage`, `renderPerformanceMetrics` в браузере | Dev HUD: FPS, Pixi contexts, доступный heap | frame time p50/p95, visible objects, Pixi children, cache size, created/destroyed | Воспроизвести `?perf=buildings`, `?perf=monsters`, `?perf=mixed`; снять Chrome Performance/Memory и сравнить с HTTP/WS за тот же интервал. Низкий FPS при нормальных HTTP/WS указывает на клиентский hot path. |

## Порядок проверки

1. Записать время, версию сборки, режим worker, сценарий, число видимых объектов и затронутый endpoint. Для HTTP сохранить `request_id` из ответа или лога.
2. Проверить доступность процесса и сигналы уровня входа: HTTP request rate/errors, p95/p99 по шаблону маршрута, WS drops/upgrades и глубину очереди. Для `/metrics` и `/api/v1/realtime` HTTP histogram не заполняется.
3. Проверить ближайший нижний слой: SQL и pool для API/worker; длительность tick и возраст очередей для simulation/outbox; браузерный frame time и heap для Pixi. Недоступные сейчас метрики не заменять выводом из общего HTTP среднего.
4. Для медленного SQL выбрать именованную операцию и воспроизвести `EXPLAIN (ANALYZE, BUFFERS)` на тестовой БД с подходящими данными. Для браузера сохранить Performance trace и число видимых объектов.
5. Зафиксировать гипотезу и результат проверки рядом с показателями до/после в журнале прогона. Цели из аудита (например, p95 viewport до 150 ms и tick меньше интервала) использовать как ориентир до замера базовой линии на нагрузке.

## Диагностика Postgres

Сначала выбрать `job` и `instance`: у API со встроенным worker один пул с пределом 20 соединений, у самостоятельного worker свой пул с таким же пределом. При двух процессах суммарно возможно до 40 соединений, не считая миграций и административных сессий. Пустые DBStats при работающем API означают запуск с in-memory fallback; проверить лог `postgres.unavailable_fallback_memory`.

Для именованной операции смотреть p95 за одинаковое окно с HTTP. Пример для чтения чанков:

```promql
histogram_quantile(0.95, sum by (le, operation) (rate(real_city_db_operation_duration_seconds_bucket{operation="world.find_chunks"}[5m])))
```

Для пула проверить `real_city_db_pool_in_use_connections / real_city_db_pool_max_open_connections`, `rate(real_city_db_pool_wait_count_total[5m])` и `rate(real_city_db_pool_wait_duration_seconds_total[5m]) / rate(real_city_db_pool_wait_count_total[5m])`. Последнее выражение дает среднее ожидание **только среди ожидавших**; при нулевом знаменателе ряд пуст. Если p95 растет вместе с ожиданием пула, выяснить, какие операции заняли соединения, прежде чем увеличивать лимит. Если ожидания нет, выбрать операцию по p95 и `result`.

| Операция | SQL и индекс для проверки |
|---|---|
| `world.find_chunks`, `world.find_chunk` | `world_chunks` по `(map_id, chunk_x, chunk_y)` и `world_tiles` по `(map_id, chunk_x, chunk_y)` из `000003_world.sql`; batch чтение использует диапазон, который может затрагивать больше строк, чем запрошено чанков. |
| `world.copy_tiles`, `world.update_tile` | Вставка tiles через `COPY`, поиск tile по `(map_id, tile_x, tile_y)`; проверить конфликт создания одного чанка несколькими запросами. |
| `building.player_placement_stats` | Агрегат по `owner_id`; `idx_buildings_owner_limit_stats` из `000018_performance_indexes.sql`. |
| `building.footprint_intersection`, `building.viewport_list` | Условия пересечения footprint в `BuildingRepo.listByViewport`; `idx_buildings_viewport`. |
| `monster.list_active_for_tick`, `monster.count_alive_by_spawn` | `idx_monsters_tick` и `idx_monsters_spawn_alive` из `000018_performance_indexes.sql`. |
| `action.fetch_due`, `outbox.fetch_due` | `idx_game_actions_due`, `idx_outbox_events_due` из `000009_simulation.sql`; учитывать блокировки `FOR UPDATE SKIP LOCKED` и размер batch. |
| `action.mark_done`, `action.mark_failed`, `outbox.mark_sent`, `outbox.mark_failed`, `outbox.mark_dead`, `building.insert` | Проверить lookup по первичному ключу, конкурирующие транзакции и ошибки; для insert — связанные индексы/ограничения. |

После выбора операции взять ее SQL из репозитория и выполнить `EXPLAIN (ANALYZE, BUFFERS)` **на тестовой БД с сопоставимыми данными и параметрами**. Сохранить план, фактические/оценочные строки, `shared hit/read`, время исполнения, сортировки и выбранный индекс. Для `UPDATE`, `INSERT` и `COPY` использовать отдельную тестовую транзакцию с откатом: `ANALYZE` действительно выполняет запрос. На живой нагрузке тяжелый `EXPLAIN ANALYZE` запускать только после отдельного решения. Для первого просмотра плана production запроса использовать обычный `EXPLAIN` без `ANALYZE` и без выполнения изменений.

Сравнить время SQL-плана с histogram: она включает ожидание свободного соединения, передачу и чтение строк, а `EXPLAIN ANALYZE` измеряет только исполнение на сервере. `world.generate_chunk` отражает CPU-генерацию, `world.copy_tiles` — запись tiles, `world.create_chunk` — полный процесс; вложенные длительности нельзя складывать как отдельные запросы.

## Проверка конфигурации и обновление панелей

Перед изменением конфигурации выполнить `bash scripts/check-observability.sh`: проверяются Compose, JSON четырех dashboards, уникальность их UID, синтаксис 53 PromQL выражений, конфигурация Prometheus и правила оповещений. Скрипт запускает закрепленный образ `prom/prometheus:v3.15.0`, если локального `promtool` нет; CI выполняет ту же проверку без запуска игрового мира. После изменения панели сохранить JSON в `deploy/observability/grafana/dashboards/`, затем перезапустить Grafana либо дождаться автоматического provisioning и проверить панель в браузере. При изменении метрики обновить каталог метрик, dashboard, alert и runbook в одном изменении.

После запуска контура проверить `make observability-targets`: `prometheus` и `api` должны быть `UP`; worker появляется только при отдельном запуске и настройке `worker-targets.yml`. В Prometheus проверить `/api/v1/rules` и запросы `up`, `real_city_http_ready`, `real_city_simulation_enabled`, `real_city_queue_snapshot_timestamp_seconds`. В Grafana открыть все четыре панели и убедиться, что источник `Prometheus` доступен. Записи результатов и сравнение с базовой линией хранить в [протоколе baseline](../performance/observability-baseline.md). Пустая серия для редкой операции сама по себе не ошибка: метрика появляется после первого события.

Данные Prometheus и Grafana находятся в именованных volumes `prometheus_data` и `grafana_data`; `observability-down` их сохраняет. Перед удалением volumes или обновлением образов экспортировать нужные временные ряды/скриншоты и сделать резервную копию volumes средствами Docker. Dashboards и конфигурация источника уже версионируются в репозитории; локальные ручные правки в Grafana могут быть заменены provisioning. Retention Prometheus ограничен 7 сутками или 2 GB. Локальные учетные данные Grafana задать через `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` до первого запуска; при уже созданном volume пароль меняется средствами Grafana. Порты интерфейсов привязаны к loopback, а API в dev Compose опубликован отдельно на всех интерфейсах: для удаленного окружения ограничить доступ к `/metrics` на proxy/сетевом уровне.

Ограничения: EventBus работает в памяти процесса и факт публикации outbox не подтверждает получение конкретным клиентом; chunk cache также живет в памяти процесса и исчезает после перезапуска. При отдельном worker использовать его собственные `job`/`instance` и не запускать вторую активную симуляцию на той же БД. Browser HUD работает только в dev и не передает телеметрию серверу; для клиентского baseline нужны сохраненные trace и скриншоты. Текущие пороги алертов предварительные до повторяемых нагрузочных замеров.

## Логи и приватность

`slog` используется для поиска конкретного запроса или действия: `request_id`, `event`, имя операции, длительность и ошибка. Метки Prometheus должны содержать только ограниченные категории. Не записывать в labels ID игрока, соединения, действия, события, чанка, сырые URL/SQL и координаты. Не публиковать `/metrics` через внешний игровой proxy.
