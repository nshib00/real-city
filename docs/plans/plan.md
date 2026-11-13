# Real City — План реализации

## Актуализация плана от 05.11.2026

По текущему коду и коммитам проверены назначенные фазы 0–4, 11, 14–18 и 21. Открытые строки этих фаз не закрываются самой сверкой: остаются SQL-конкурентные сценарии, живая браузерная и мобильная приёмка, производительные замеры, полное покрытие ассетов и проверка выпуска. Подробный остаток и границы проверки записаны в [журнале фаз J](../status/j-phases.md). Пункт 29 дополнил план задачами из текущей очереди; это не означает выполнения пунктов 20–28.

Профильные агрегированные оценки удалены по пункту очереди 1 (`169558b`). Требование 1.23 исключено; связанные строки фазы 1 и зависимостей больше не требуют этих оценок. Изменения дорог (`d708b59`), сторожевой башни (`14ac8be`, `51c05a0`, `207ba7e`, `f5d09ad`), звука (`119bbd7`, `8614791`) и серверного ограничения зданий 1×1 (`d9f68ba`) учтены ниже только в соответствующих частичных статусах. Обнаружение монстров башней на сервере и клиентское удаление поддержки больших построек остаются отдельными задачами.

## Дополнение от 03.11.2026: модели дорог

Выпущен новый визуальный набор для трёх видов дорог — грунтовой, обычной и мостовой. Для каждого вида созданы 16 вариантов стыковки и четыре состояния (`active`, `construction`, `damaged`, `ruined`): всего 192 PNG и 192 GLB. Генератор, проверка портов и состав выпуска описаны в [плане редизайна дорог](../assets/roads-redesign.md) и [журнале ассетов](../assets/asset-generation-status.md).

Наборы подключены в runtime по существующим именам ассетов с новой ревизией URL; сборщик сохраняет GLB, а прежний отдельный тайл `terrain/road` удалён. Валидатор проверил 192 варианта и геометрию границ; профильные frontend-проверки и `npx vite build` прошли. Композиция PNG подтверждает отсутствие щели в переходе грунт → обычная → мостовая, но смешанную сеть на работающей карте отдельно не принимали. Поэтому обновлён только статус дорожной части фазы 22; общий охват ассетов и приёмка фазы остаются частичными.

## Дополнение от 01.11.2026: очередь 111–120

[Очередь 111–120](queue-111-120.md) ограничивает production CORS доменом выпуска, выносит TTL токенов в Compose, задаёт proxy timeout и добавляет локальную проверку разрешённого/чужого Origin. Добавлены workflow сборки, сканирования и публикации образов, инструкция безопасности и команды оператора. Фактические результаты и ограничения — в [отчёте](queue-111-120-implementation.md). Внешняя выкладка, запуск workflow в GitHub и откат на предыдущие образы этим изменением не подтверждаются; широкие строки остаются частичными.

Пунктов плана выполнено: 175/361 активных (48.5%). Частично: 163; ожидает реализации: 23; исключены: 14. Всего строк задач: 375.

План охватывает весь путь от текущего игрового прототипа до проверенного выпуска. ✅ означает завершённую работу, ⏳ — оставшуюся, 🟡 — реализованную частично, 🚫 — исключённую из актуального направления. В числителе учитываются только ✅; исключённые пункты остаются в истории плана, но не становятся задачами к выполнению. Пути в таблицах указаны от корня репозитория. Фазы 21–27 раскрывают крупные задачи существующих фаз; одна и та же работа не считается завершённой дважды без результата и проверки из соответствующей строки.

## Дополнение от 01.11.2026: очередь 101–110

[Очередь 101–110](queue-101-110.md) и [фактический отчёт](queue-101-110-implementation.md): ограничено время `/ready` при зависшем PostgreSQL, исправлена выдача `/metrics` через SPA fallback, проверены HTTPS redirect, заголовки, лимит API-тела и штатный SIGTERM API в одноразовом Compose. Лимиты HTTP/WS/БД/симуляции вынесены в production-конфигурацию. Откат на старые образы и внешний стенд остаются открытыми; большие строки плана сохраняют частичный статус.

## Дополнение от 01.11.2026: очередь 91–100

[Очередь 91–100](queue-91-100.md) и [фактический отчёт](queue-91-100-implementation.md): прошли frontend quality gate, изолированные SQL/Redis-интеграционные тесты и одноразовая production-репетиция с HTTPS, API/WS, сбоями хранилищ, восстановлением дампа и игровым рестартом. Frontend-образ и production Compose проверены в контейнерах; пункты 18.2 и 18.3 закрыты. При паузе БД API может отвечать только по таймауту; откат на прошлый релиз, внешний TLS и браузерная/мобильная приёмка остаются открытыми.

## Дополнение от 01.11.2026: очередь 81–90

[Очередь 81–90](queue-81-90.md) и [отчёт о выполнении](queue-81-90-implementation.md): проверены обновление схемы 48→53 с сохранением данных и повтором мигратора, игровой restart-сценарий, свежесть контрактов и короткие HTTP/WS-нагрузки. Добавлены безопасный production-журнал паники, healthcheck backend-образа и шаблон переменных выпуска; ручной чеклист обновлён без заявления о прохождении desktop/mobile. Пункты 17.4 и 18.1 закрыты по результатам тестов и контейнерной проверки. SQL-конкурентная, длительная нагрузочная и production-приёмка остаются открытыми.

## Дополнение от 01.11.2026: очередь 71–80

[Очередь 71–80](queue-71-80.md) и [фактический отчёт](queue-71-80-implementation.md) закрывают конкретные серверные регрессии и проверки: Go 1.24.13 `build`/`vet`/полный `test`/`race`, миграции 1–53 в изолированной БД с повторным запуском, тесты кеша ответов и AI, живой API/WS smoke и защиту dry-run архиватора. Исправлены устаревший тест каталога и таймаут смены пароля на медленном CPU. Открытая приёмка 31–40, нагрузка AI/WS и production-откат остаются. Эта очередь сама по себе не меняла статусы больших строк плана; текущий счётчик выше учитывает завершённые позже пункты очереди 81–90.

## Актуализация на 30.10.2026

Очереди из переписки: [пункты 1–20](queue-20-implementation.md) и [пункты 21–30](queue-21-30-implementation.md). Обе выполнены частично. Исторический frontend-прогон (31.10.2026): **370/370 тестов, 94 файла; проверка типов и production-сборка успешны**. На момент той сверки сервер не пересобирался и миграции `000049` и `000050` не применялись к рабочей БД; последующие изолированные прогоны не подтверждают состояние рабочей БД.

Очередь приёмки: [пункты 31–40](queue-31-40.md), с отдельными критериями приёмки. Она раскрывает остаток предыдущих очередей, не меняя их статусы.

Текущая очередь разработки: [пункты 41–50](queue-41-50.md) — выполнена частично; [отчёт](queue-41-50-implementation.md) перечисляет изменения профилей и непрочитанного, документацию, подготовку визуальных сценариев и незавершённые серверные пункты. Она не отменяет незавершённую приёмку очереди 31–40.

Очередь [51–60](queue-51-60.md) начата частично: клиентские координаты и диагностика, исправление дедупликации звука, инструмент анализа источников рецептов, подготовка защиты и локальных проверок/образов. [Фактический отчёт](queue-51-60-implementation.md) перечисляет нереализованные части и непрошедшую приёмку. Остаток 31–50 сохраняет приоритет; счётчики не меняются.

Дополнение от 31.10.2026: [очередь 61–70](queue-61-70.md) выполнена частично — переключаемая тема, форматирование HUD, семантика категорий, защита контекста инспектора/чата, жесты, координатный осмотр, матрица визуального каталога и ограниченные повторы загрузки PNG. [Отчёт](queue-61-70-implementation.md) разделяет реализацию и остаток по всем десяти пунктам. Браузерная/мобильная/художественная приёмка, скринридер, полная упаковка атласов и управление GPU-памятью не завершены. Незавершённые пункты 31–60 сохраняют приоритет, счётчики не меняются.

По очереди 31–40 подготовлены дополнительные инструменты миграционной и production-приёмки, исправлен WS-клиент проверок и расширены CI-артефакты. [Результаты и ограничения](queue-31-40-implementation.md): серверная/SQL/браузерная/production-приёмка остаётся открытой; счётчик завершённых задач не увеличен.

Приоритет оставшейся работы:

1. Повторить build/vet/test/race и проверку актуальных миграций в изолированном окружении с Go и PostgreSQL, включая повторный запуск мигратора; исправить обнаруженные ошибки. Исторический прогон миграций до 53 не подтверждает состояние изменившегося кода и рабочей базы.
2. Пройти SQL-конкурентные и restart-сценарии: производство, поля, строительство, ремонт, атаки, рынок, XP и события после commit.
3. Подтвердить PvP-защиту, управление аккаунтами/отзыв HTTP- и WS-доступа, все производственные цепочки и матрицу жизненного цикла построек/обороны.
4. Выполнить живые desktop/mobile E2E с настоящими API/WS; подготовленные сценарии пока не приняты.
5. Получить реальные HTTP/WS/тик/CPU/RAM и клиентские замеры, затем оптимизировать подтверждённые узкие места и повторить измерения.
6. Выполнить production-репетицию, HTTPS, backup/restore и откат на конкретный предыдущий релиз с проверкой совместимости схемы.

Сверка выполнена по текущему рабочему дереву, включая незакоммиченные изменения прямого PvP и ассетов. Это инвентаризация реализации, а не подтверждение production-приёмки. ✅ означает реализованный ограниченный результат строки; 🟡 — существующая реализация с явно указанным остатком или незавершённой проверкой; ⏳ — работа ещё впереди. Пути к будущим файлам являются целевыми, а не утверждением об их наличии. Исторические успешные прогоны не заменяют проверку изменившейся реализации. Счётчик строк отражает покрытие плана, а не процент готовности продукта: фазы 21–26 содержат детализацию/приёмку результатов предыдущих фаз.

Актуальное направление: одна общая карта, строительство на свободной допустимой клетке, владение объектами и конкуренция за ресурсы. Контролируемая территория исключена. PvP — инвентарное оружие/бомбы и созданные игроками монстры; рейдов, путешествия рейдового отряда и рейдовой добычи в целевом объёме нет. Источник решения — `AGENTS.md`, `docs/game-design/player-conflict.md`, `pvp.go` и действующий router. Старые строки фазы 10 переопределены с сохранением номеров.

Последние подтверждённые проверки (frontend — в отчёте 61–70, остальные — в отчётах 21–40):

- Фронтенд: 370 тестов в 94 файлах, проверка типов и production-сборка проходят.
- Контракты: OpenAPI содержит 79 HTTP-операций, включая health/readiness/metrics/Swagger; runtime freshness и маршрутная проверка пройдены с Go. Размеры мира и события согласованы.
- Каталоги: 72 обычных типа построек, 80 ресурсов; balance snapshot и runtime-таблицы согласованы, ошибок покрытия нет.
- XP: 84 типа, 474 уровня, 74 документа; `make catalog-check` подтверждает синхронизацию таблиц. Вероятности альтернативных редких выходов валидированы.
- 03.11.2026: после установки Go прошли `go test ./...` в backend, генерация OpenAPI и PostgreSQL/Redis integration test через Testcontainers; HTTP router smoke и полное сравнение OpenAPI snapshot входят в успешный Go-прогон.
- Живые браузерные сценарии, длительная нагрузка, внешний TLS и production backup/restore на целевом стенде остаются непроверенными. Локальная репетиция TLS и backup/restore и короткие нагрузочные прогоны были выполнены; художественная/звуковая приёмка и проверка на реальных мобильных устройствах открыты.

| Фаза | Результат сверки и следующий критерий |
|---|---|
| 0 | Каркас есть; local Compose не равен готовому production-окружению. |
| 1 | Auth, базовый профиль и единый каталог уровней есть; расширенный публичный профиль и XP-антифарм предстоит завершить. |
| 2 | Pixi/координаты/чанки есть; wrap уже частично работает, нужна сквозная проверка швов и путей. |
| 3 | Панели, MapWidget, unread и Playwright runner есть; Storybook и приёмка адаптивности остаются. |
| 4 | Строительство/апгрейды/лимиты есть; таблицы существуют, актуальная каталожная и транзакционная проверка ещё нужна. |
| 5 | Рецепты шахты (12 уровней) и канатного двора (8) добавлены; транзакции производства/полей и сквозная экономика требуют серверного прогона. |
| 6 | WS gateway/client/events реализованы; социальная доставка не завершена и учитывается в 11.9. |
| 7 | Очереди/worker/outbox реализованы; рестарт и конкурентные новые PvP-действия требуют актуального прогона. |
| 8 | Базовые монстры/PvE реализованы; все защитники/ассеты/расширенная оборона не закрываются этим статусом. |
| 9 | Исключена; владение отдельной постройкой/ресурсом не возвращает контролируемую территорию. |
| 10 | Прямой PvP и платный таймерный worker-ремонт реализованы; серверный прогон и полный anti-abuse ещё нужны. |
| 11 | PostgreSQL SocialRepo, leave/kick/leadership, WS, unread и auto-match реализованы; SQL/live приёмка и полный контур модерации остаются. |
| 12 | Router/idempotency/client/snapshot есть; свежесть полного контракта прямого PvP требует проверки. |
| 13 | Управление аккаунтами, роли, отзыв сессий и аудит реализованы; серверная приёмка, диагностика и полный контур модерации остаются. |
| 14 | Значительная часть пайплайна/ассетов/loader уже есть; полное покрытие и приёмка остаются. |
| 15 | Canvas/visibility/texture cache, Redis chunk cache, coalescing и диагностика есть; нагрузочные замеры и итоговая оптимизация не готовы. |
| 16 | Исторические Go/SQL/Redis и frontend 370/370 прогоны есть; текущие правки и live desktop/mobile приёмка остаются. |
| 17 | HTTP/WS/DB/worker метрики и dashboards реализованы; игровые/client/Redis метрики и централизованные логи остаются. |
| 18 | Frontend image, Caddy HTTPS/WS, production Compose и backup/restore прошли локальную контейнерную репетицию; внешний стенд и откат на прошлый релиз не выполнены. |
| 19 | Frontend/backend/contracts/browser CI и production-rehearsal добавлены; успешные серверные jobs и CD ещё не приняты. |
| 20 | README и часть архитектурных/операционных документов есть; финальная сверка/руководства/паспорт отсутствуют. |
| 21 | Реестры 72 типов и 80 ресурсов, включая башню L1–L6, вновь синхронизированы; `make catalog-check` проходит. Экономический сценарий без тупиков не принят. |
| 22 | Большинство семейств и пайплайн существуют; для трёх видов дорог выпущен и подключён полный набор форм/состояний, но охват остальных семейств, каталожная сверка и общая модельная приёмка остаются. |
| 23 | Записи, импорт/сборка, Web Audio и wiring уже есть; художественная, мобильная и итоговая событийная приёмка остаётся. |
| 24 | Есть исходный UI/style guide и звуковой отклик; завершённого редизайна/доступности/сравнения до–после нет. |
| 25 | Транзакции игровых действий, PvP-защита, рецепты и управление аккаунтами реализованы; SQL/race/restart и цельный игровой цикл не приняты. |
| 26 | Частичные метрики/сборки/документы есть; production-выпуск и многопользовательская приёмка не выполнены. |

## Предыдущая очередь из 10 задач — 30.10.2026

Код добавлен по всем десяти выбранным задачам. Более широкие строки фаз не закрываются автоматически: серверная компиляция, миграции и живой сценарий пока не проверены в этом окружении. Правила и команды приёмки: [социальный контур и ремонт](../qa/social-and-repair.md).

| Выбранная задача | Результат |
|---|---|
| `16.10` | Исправлен URL спрайта; тест и полный frontend suite проходят. |
| `11.3` | PostgreSQL SocialRepo и выбор адаптера в API; SQL integration test сохранности данных. |
| `11.18` | Транзакции reserve/create и cancel/refund, блокировки, rollback/race tests; общий memory gate. |
| `11.4` | Leave/kick, передача лидерства, роспуск последним лидером, UI и серверные проверки прав. |
| `11.9` | EventBus/WS события после commit, private fanout текущим участникам, обновление кешей/reconnect. |
| `11.11` | Постоянные read cursors, unread, видимый активный канал и frontend-тест. |
| `1.20` | Один JSON-каталог, generated Go, shared TS, иконки, roadmap открытий, API и проверка свежести. |
| `10.6` | Quote/status, материалы/рабочий/таймер, постоянная очередь, worker completion, возврат рабочего, UI и тесты. |
| `24.10` | Начальный фокус, Tab/Shift+Tab, Escape и возврат фокуса в Modal; keyboard test. |
| `25.10` | Двухэтапный сценарий настоящего API/WS с рестартом; запуск заблокирован Docker, приёмка не заявлена. |

## Подход к логированию

Текущее состояние: реализованы API, авторизация, общая карта, строительство, экономика, симуляция, WebSocket, базовый социальный контур, прямые PvP-атаки, аудио и локальная наблюдаемость. Социальный контур использует PostgreSQL при настроенной БД; memory остаётся режимом без БД. Игровые системы и контент требуют сквозной приёмки. Структурированные логи уже есть в сервисах, middleware и worker; оставшиеся задачи — полнота событий и проверка эксплуатационных сценариев. Для multiplayer-стратегии логирование должно покрывать не только HTTP-запросы, но и realtime-события, симуляцию мира, экономику, бои, фоновые задачи, ошибки клиентов и административные действия.

Целевая модель, которую нужно сохранять и дополнять:

- HTTP middleware: единый access log для каждого запроса (`request_id`, `method`, `path`, route pattern, `status`, `duration_ms`, `player_id`, `ip`, `user_agent`, размер ответа, error class без PII).
- WebSocket gateway: lifecycle соединений (`connected`, `authenticated`, `subscribed`, `disconnected`), latency ping/pong, dropped messages, backpressure, reconnect и ошибки протокола.
- Service layer: бизнес-события (`player.registered`, `player.profile_updated`, `player.xp_awarded`, `player.level_changed`, `building.placed`, `building.completed`, `resource.harvested`, `field.harvested`, `oil_well.claimed`, `fuel.consumed`, `ruin.captured`, `alliance.created`, `combat.resolved`, `monster.moved`, `combat.building.damaged`, события создания игроком монстра) с идентификаторами сущностей и без секретов.
- Simulation layer: ticks, чанки, очереди действий, deterministic decisions, slow tick warnings, degraded режимы и конфликтующие команды игроков.
- Adapter layer: технические события внешних систем (`postgres`, `redis`, `storage`, `worker`, `websocket`, `asset_pipeline`) — latency, retries, degraded fallback, provider status/error code.
- Domain layer остаётся без логгера и внешних зависимостей.
- Все новые логи должны быть структурированными, с постоянными именами полей и event-name в поле `event`.

## Фаза 0 — Инфраструктурный каркас

| # | Что | Файлы | Статус |
|---|---|---|---|
| 0.1 | Монорепозиторный каркас: `frontend`, `backend`, `shared`, `docs`, единые README и команды разработки | `frontend/`, `backend/`, `shared/`, `README.md`, `Makefile` | ✅ |
| 0.2 | Backend Go module, базовая структура clean/hexagonal architecture, `cmd/api`, `internal/domain`, `internal/service`, `internal/adapter` | `backend/go.mod`, `backend/cmd/api/`, `backend/internal/` | ✅ |
| 0.3 | Frontend Vite + React + TypeScript, strict TS config, базовая структура `app`, `features`, `game`, `shared` | `frontend/package.json`, `frontend/src/`, `frontend/tsconfig.json`, `frontend/vite.config.ts` | ✅ |
| 0.4 | Конфигурация backend: `Config` для server, postgres, redis, JWT/session, websocket, simulation, storage, observability | `backend/pkg/config/config.go`, `backend/.env.example` | ✅ |
| 0.5 | Логгер backend: `slog` JSON в production, text в development, stable fields, helpers для безопасных error attrs | `backend/pkg/logger/` | ✅ |
| 0.6 | Ошибки приложения: типы `NotFound`, `Conflict`, `Forbidden`, `Unauthorized`, `BadRequest`, `Validation`, `RateLimited`; маппинг на HTTP/WS errors | `backend/pkg/apperror/`, `backend/internal/adapter/http/response.go`, `backend/internal/adapter/ws/error.go` | ✅ |
| 0.7 | Подключение к PostgreSQL: pool, ping, migrations bootstrap, graceful close | `backend/internal/adapter/postgres/db.go`, `backend/db/migrations/` | ✅ |
| 0.8 | Подключение к Redis: client, ping, namespaces для cache/session/realtime, graceful close | `backend/internal/adapter/redis/client.go` | ✅ |
| 0.9 | HTTP-ответы и request decoding: `JSON`, `Error`, validation errors, pagination helpers | `backend/internal/adapter/http/` | ✅ |
| 0.10 | `main.go` + `app.go`: DI каркас, lifecycle, graceful shutdown HTTP/WS/workers | `backend/cmd/api/` | ✅ |
| 0.11 | Docker compose для local dev: backend, frontend, postgres, redis, optional storage, healthchecks и volumes | `docker-compose.yml`, `docker-compose.dev.yml` | 🟡 local/dev Compose и отдельный production Compose с frontend/Caddy есть; production-контейнеры проверены в одноразовой репетиции, но полный local/dev сценарий строки не принят |
| 0.12 | Базовый frontend shell: первый экран как игровая поверхность, root layout, providers, error boundary | `frontend/src/app/`, `frontend/src/main.tsx` | ✅ |
| 0.13 | Design tokens и базовые стили: палитра, размеры панелей, typography, z-index слои, CSS reset | `frontend/src/app/styles/`, `frontend/src/shared/ui/` | ✅ |
| 0.14 | Shared contract package: общие enum/types для координат, чанков, объектов, событий, ошибок API | `shared/`, `frontend/src/shared/api/`, `backend/internal/contract/` | ✅ |
| 0.15 | Unit-тесты инфраструктурного каркаса: config, errors, logger helpers, HTTP responses, координатные helpers | `backend/**/*_test.go`, `frontend/src/**/*.test.ts` | ✅ |

---

## Фаза 1 — Аккаунты, игроки и сессии

| # | Что | Файлы | Статус |
|---|---|---|---|
| 1.1 | Domain: `Player`, `Profile`, `Session`, статусы игрока, базовые настройки профиля | `backend/internal/domain/player/` | ✅ |
| 1.2 | Миграции users/players/profiles/sessions с уникальными email/name и timestamps | `backend/db/migrations/` | ✅ |
| 1.3 | SQL-запросы и Postgres-репозитории players/profiles/sessions | `backend/db/query/player.sql`, `backend/internal/adapter/postgres/player_repo.go` | ✅ |
| 1.4 | Хэширование паролей через bcrypt, policy длины и сложности | `backend/internal/domain/player/password.go` | ✅ |
| 1.5 | JWT/session manager: access token, refresh token, rotation, blacklist/revoke | `backend/internal/adapter/jwt/`, `backend/internal/adapter/redis/session_store.go` | ✅ |
| 1.6 | `service/auth`: register, login, refresh, logout, logout all devices | `backend/internal/service/auth.go` | ✅ |
| 1.7 | `service/player`: get/update profile, change password, avatar/settings | `backend/internal/service/player.go` | ✅ |
| 1.8 | DTO auth/player и validation tags | `backend/internal/adapter/http/dto/auth.go`, `backend/internal/adapter/http/dto/player.go` | ✅ |
| 1.9 | Handler auth: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | `backend/internal/adapter/http/handler/auth.go` | ✅ |
| 1.10 | Handler player: `GET /players/me`, `PATCH /players/me`, `PATCH /players/me/password`, `DELETE /players/me` | `backend/internal/adapter/http/handler/player.go` | ✅ |
| 1.11 | Middleware auth/role: userID/playerID в context, admin checks, WS auth reuse | `backend/internal/adapter/http/middleware/auth.go`, `backend/internal/adapter/ws/auth.go` | ✅ |
| 1.12 | Frontend auth flow: login/register screens, token storage strategy, protected app route, logout | `frontend/src/features/auth/`, `frontend/src/shared/api/client.ts` | ✅ |
| 1.13 | Frontend profile panel: имя игрока, avatar placeholder, настройки уведомлений/качества рендера | `frontend/src/features/player/` | ✅ |
| 1.14 | Unit-тесты `service/auth` и session store | `backend/internal/service/auth_test.go`, `backend/internal/adapter/redis/tests/` | ✅ |
| 1.15 | Unit-тесты HTTP auth/player handlers и auth middleware | `backend/internal/adapter/http/handler/`, `backend/internal/adapter/http/middleware/` | ✅ |
| 1.16 | Frontend tests auth store, API client interceptors, protected route | `frontend/src/features/auth/**/*.test.tsx`, `frontend/src/shared/api/**/*.test.ts` | ✅ |
| 1.17 | Событийное логирование auth/player: register/login/logout/refresh, failed auth, profile update, password change; без email/token в логах | `backend/internal/service/auth.go`, `backend/internal/service/player.go` | ✅ |
| 1.18 | Расширенная модель профиля из `docs/game-design/user-profile-and-levels.md`: публичная и приватная части, `avatarId`, `bannerId`, `title`, `level`, `xp`, `groupId`, `homeCenterId` и правила скрытия точных ресурсов/уязвимостей | `backend/internal/domain/player/profile.go`, `backend/internal/contract/types.go`, `shared/src/index.ts` | 🟡 appearance, title, home center и group реализованы; публичный ответ скрывает приватные поля и точные координаты; расширенные значки и SQL/live проверка остаются. Агрегированные оценки удалены (`169558b`) |
| 1.19 | Миграции и репозитории для расширенного профиля: профильные поля, XP events, badges, featured badges, milestones, last seen с публичным округлением | `backend/db/migrations/`, `backend/db/query/player_profile.sql`, `backend/internal/adapter/postgres/player_profile_repo.go` | 🟡 миграция 000019_xp_events.sql и AwardXPEvent есть; badges/milestones и публичное округление last seen отсутствуют |
| 1.20 | Каталог уровней 1-15: пороги опыта, названия, `lucide-react` иконки, открытия по уровням, progress model с `nextLevelXp: null` на максимальном уровне | `data/player/levels.json`, `tools/player/generate_levels.py`, `backend/internal/domain/player/levels.generated.go`, `shared/player/levels.ts`, `frontend/src/features/player/levels.ts` | ✅ единый data/player/levels.json, generated Go + freshness check, shared TS, lucide icons и API /players/levels; progress/null проверены frontend-тестом; будущие открытия явно помечены planned, игровых ограничений каталожная задача не вводит |
| 1.21 | `service/profile`: сборка собственного и публичного профиля, расчет прогресса уровня, выбранных значков, публичной активности, примерной области города и приватных настроек | `backend/internal/service/profile.go`, `backend/internal/service/player.go` | 🟡 GetMe/GetPublic и уровень есть; расширенная сборка/значки/активность отсутствуют |
| 1.22 | `service/xp`: серверное начисление опыта только после завершенных действий, auditable log, soft caps, убывающая отдача и антифарм для связанных/повторяемых действий | `backend/internal/service/experience.go`, `backend/internal/adapter/postgres/player_repo.go`, `backend/db/migrations/000019_xp_events.sql` | 🟡 UTC daily caps, diminishing returns, requested/actual audit и идемпотентность реализованы; исторический общий Go-прогон есть, но актуальные SQL/anti-farm сценарии требуют приёмки |
| 1.23 | Агрегированные числовые оценки профиля | — | 🚫 исключено по пункту очереди 1; реализация удалена коммитом `169558b`, возвращать проекции не требуется |
| 1.24 | API профиля: `GET /players/{id}/profile` для публичной карточки, `GET /players/me/profile` для своего профиля, `PATCH /players/me/profile` для титула, аватара, баннера и закрепленных значков | `backend/internal/adapter/http/handler/player.go`, `backend/internal/adapter/http/dto/player.go`, `frontend/src/shared/api/player.ts` | 🟡 GET /players/{id} отдаёт безопасный базовый DTO; целевые /profile и расширенное редактирование не реализованы |
| 1.25 | Интеграция XP с игровыми событиями: строительство, апгрейды, удержание ресурсных узлов, логистика, оборона, PvE, торговля, групповой вклад и исследование | `backend/internal/service/building.go`, `backend/internal/service/resource.go`, `backend/internal/service/combat.go`, `backend/internal/service/alliance.go`, `backend/internal/service/market.go` | 🟡 XP подключён к завершению строительства/производства, сбору полей и ресурсам; остальное требует интеграции |
| 1.26 | Frontend экран своего профиля: уровень, прогресс до следующего, открытые возможности, закрепленные значки, недавние события и подсказки по XP | `frontend/src/features/player/ProfilePanel.tsx`, `frontend/src/features/player/ProfileScreen.tsx`, `frontend/src/features/player/profileApi.ts` | 🟡 ProfilePanel использует общий каталог, показывает уровень/XP/иконку и планируемые возможности; достижения, значки и история ещё нужны |
| 1.27 | Frontend публичная карточка чужого игрока из карты/инспектора: имя, аватар, уровень, титул, группа, примерная зона поселения, публичные специализации и достижения | `frontend/src/features/player/PublicProfileCard.tsx`, `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/world-map/` | 🟡 PlayerBalloon и базовый публичный DTO существуют; расширенная карточка с группой и достижениями отсутствует |
| 1.28 | UI бейджей, milestone-истории, репутации и дипломатических меток: 3-5 закрепленных значков, публичные теги торговец/защитник/исследователь/атакующий/строитель | `frontend/src/features/player/BadgesPanel.tsx`, `frontend/src/features/player/MilestonesPanel.tsx`, `frontend/src/features/player/ReputationTags.tsx` | ⏳ |
| 1.29 | Тесты backend для уровней, XP caps, приватности публичного профиля и audit log начислений опыта | `backend/internal/domain/player/*_test.go`, `backend/internal/service/profile_test.go`, `backend/internal/service/xp_test.go` | 🟡 player/experience тесты есть; актуальные caps, публичная приватность и audit log ещё требуют полного прогона |
| 1.30 | Тесты frontend для своего/публичного профиля, прогресса уровня, скрытия приватных данных, выбора featured badges и responsive-состояний | `frontend/src/features/player/**/*.test.tsx`, `frontend/src/shared/api/player.test.ts` | 🟡 ProfilePanel.test.tsx есть; публичная карточка/значки/приватность ещё не реализованы |
| 1.31 | Утвердить оригинальные названия статусов игроков и создать различимые иконки для каждого уровня; подключить их во всех местах отображения уровня и проверить читаемость | `docs/game-design/player-status-levels-proposal.md`, `docs/assets/player-level-emblems.md`, `frontend/src/features/player/`, `data/player/levels.json` | 🟡 предложения названий и подробное Blender-ТЗ подготовлены; утверждение, изготовление и подключение иконок остаются |

---

## Фаза 2 — Мировая карта, координаты и чанки

| # | Что | Файлы | Статус |
|---|---|---|---|
| 2.1 | Domain: `WorldMap`, `Chunk`, `Tile`, координаты grid/isometric, terrain types | `backend/internal/domain/world/`, `shared/world/` | ✅ |
| 2.2 | Миграции world_maps/chunks/tiles с индексами по координатам и версии чанка | `backend/db/migrations/` | ✅ |
| 2.3 | SQL-запросы и Postgres-репозитории world/chunk/tile | `backend/db/query/world.sql`, `backend/internal/adapter/postgres/world_repo.go` | ✅ |
| 2.4 | Генератор стартового мира: seed terrain, стартовые зоны, нейтральные ресурсы, безопасные области | `backend/internal/service/worldgen/`, `backend/cmd/seed/` | ✅ |
| 2.5 | `service/world`: get chunk, list visible chunks, claim/load viewport, chunk versioning | `backend/internal/service/world.go` | ✅ |
| 2.6 | HTTP endpoints: `GET /world`, `GET /world/chunks?x=&y=&radius=`, `GET /world/viewport` | `backend/internal/adapter/http/handler/world.go`, `backend/internal/adapter/http/dto/world.go` | ✅ |
| 2.7 | Frontend PixiJS stage: canvas mount, renderer lifecycle, resize, devicePixelRatio, ticker control | `frontend/src/game/renderer/` | ✅ |
| 2.8 | Isometric camera: pan, zoom, bounds, screen↔tile conversion, keyboard/mouse controls | `frontend/src/game/camera/`, `frontend/src/game/coordinates/` | ✅ |
| 2.9 | Terrain renderer: слои terrain/roads/buildings/units/effects/overlays, depth sort по iso координате | `frontend/src/game/layers/`, `frontend/src/game/renderers/terrain.ts` | ✅ |
| 2.10 | Chunk loader на клиенте: TanStack Query cache, prefetch соседних чанков, unload дальних чанков | `frontend/src/features/world/`, `frontend/src/shared/api/world.ts` | 🟡 Query cache и gcTime есть; отдельные prefetch соседей и выгрузка по расстоянию не подтверждены |
| 2.11 | Hover/selection пустого тайла, координаты в inspector, debug overlay для grid/chunk bounds | `frontend/src/features/selection/`, `frontend/src/game/overlays/` | ✅ |
| 2.12 | Unit-тесты координат, chunk math, visibility queries и world service | `backend/internal/domain/world/`, `frontend/src/game/**/*.test.ts` | ✅ |
| 2.13 | Логирование загрузки чанков: viewport requests, cache hit/miss, slow chunk queries, oversized radius | `backend/internal/service/world.go`, `backend/internal/adapter/http/handler/world.go` | ✅ |
| 2.14 | Цикличный мир: toroidal wrap координат по X/Y, нормализация чанков/тайлов, кратчайшие пути через границу карты | `backend/internal/service/world.go`, `backend/internal/service/worldgen/generator.go`, `frontend/src/game/coordinates/iso.ts`, `backend/internal/service/pvp.go` | 🟡 единые wrap/distance helpers, нормализация мира и footprint на швах; добавлен тест пути монстра, серверный прогон остаётся |
| 2.15 | Укрупнение тайлов примерно в 3 раза: единый `tileSize`, пересчёт iso projection, camera zoom bounds, hit testing и selection | `frontend/src/game/coordinates/iso.ts`, `frontend/src/game/renderer/PixiStage.tsx`, `frontend/src/game/IsoMap.tsx`, `frontend/src/app/styles/index.css` | ✅ |
| 2.16 | Viewport/chunk loading для цикличной карты: корректная загрузка чанков на швах мира и отсутствие дублей при wrap-around | `backend/db/query/world.sql`, `backend/internal/service/world.go`, `frontend/src/features/world/` | 🟡 чанки и тайлы нормализуются и дедуплицируются на клиенте/сервере; frontend-тесты проходят, живая приёмка швов остаётся |
| 2.17 | Уменьшение количества рек и гор примерно в 5 раз по сравнению с текущей генерацией, проверка тестом плотности terrain | `backend/internal/service/worldgen/generator.go`, `backend/internal/service/worldgen/generator_test.go` | ✅ |
| 2.18 | Реализовать высоту объектов: данные и совместимую миграцию, порядок перекрытия на карте и серверные правила перелёта монстров; проверить швы и препятствия | `docs/game-design/object-height-plan.md`, `backend/internal/`, `frontend/src/game/` | 🟡 план механики подготовлен; реализация и сквозная приёмка остаются |
| 2.19 | Добавить бирюзовый хвойный и густой оранжевый лес: генерацию, число ударов, награды и вероятности, сохранение прогресса рубки и восстановление | `docs/game-design/forest-variants-plan.md`, `docs/assets/forest-variant-modeling-plan.md`, `backend/internal/`, `frontend/src/game/` | 🟡 механика и моделирование трёх состояний описаны; игровые данные, ассеты и проверка не завершены |

---

## Фаза 3 — Игровой HUD и базовый UI

| # | Что | Файлы | Статус |
|---|---|---|---|
| 3.1 | Верхняя панель ресурсов: население/рабочие, монеты, эолийские кристаллы, основные материалы, нефть/бензин и статус защиты | `frontend/src/features/hud/ResourceBar.tsx`, `frontend/src/app/styles/index.css` | ✅ |
| 3.2 | Левая панель инструментов: selection, build, road, repair, прямая атака через инспектор; стены создаются через категорию `Оборона` в меню строительства | `frontend/src/features/tools/ToolBar.tsx`, `frontend/src/features/buildings/BuildMenu.tsx` | ✅ |
| 3.3 | Правый inspector: selected tile/object/player, tabs, actions, health/owner/production blocks | `frontend/src/features/inspector/` | ✅ |
| 3.4 | Нижний event log/chat shell: события системы, сообщения игрока, unread indicator | `frontend/src/features/event-log/`, `frontend/src/features/chat/` | 🟡 журнал/чат и счётчики непрочитанного в `EventLog`/`ChatPanel` есть; живая синхронизация read cursor после reconnect ещё требует приёмки |
| 3.5 | Notification system: toast/feed, severity, batching realtime событий | `frontend/src/features/notifications/` | ✅ |
| 3.6 | Modal/drawer primitives, icon buttons, tooltips, segmented controls, tabs, menus | `frontend/src/shared/ui/` | ✅ |
| 3.7 | Zustand/Jotai stores: tool mode, selection, viewport, UI preferences, realtime status | `frontend/src/shared/store/`, `frontend/src/game/state/` | ✅ |
| 3.8 | Responsive layout: desktop panels, compact mobile/tablet fallback, no text overlap | `frontend/src/app/styles/layout.css`, `frontend/src/features/hud/` | 🟡 адаптивные стили есть; отсутствие перекрытий на целевых размерах не подтверждено |
| 3.9 | Empty/loading/error states для карты, API, WS reconnect и authorization | `frontend/src/app/`, `frontend/src/shared/ui/StatusState.tsx` | ✅ |
| 3.10 | Storybook или Ladle для ключевых UI-состояний strategy interface | `frontend/.storybook/` или `frontend/src/stories/` | 🟡 StrategyInterface.stories.tsx есть; зависимости/команда запуска Storybook или Ladle отсутствуют |
| 3.11 | Component/unit tests для HUD, toolbar, inspector, stores | `frontend/src/**/*.test.tsx` | ✅ |
| 3.12 | Playwright visual smoke: первый экран, desktop/mobile, карта не пустая, панели не перекрывают критичный контент | `frontend/tests/e2e/ui.spec.ts` | 🟡 Playwright 1.62.1, config и runner в `frontend/package.json` подключены; сценарии и snapshots есть, но живой desktop/mobile прогон с текущим API/WS не принят |
| 3.13 | UI полного списка ресурсов: раскрываемый реестр ресурсов, категории, лимит только для монет, редкие супер-ресурсы, топливо и фильтры | `frontend/src/features/resources/`, `frontend/src/features/hud/ResourceBar.tsx` | ✅ |
| 3.14 | UI союзов: экран Союзного дома, роли, участники, казна, пожертвования, расходы и общие баффы | `frontend/src/features/alliance/` | 🟡 панель союза/казны/баффов есть; расходы и полный набор членских операций не завершены |
| 3.15 | Виджет карты: кнопка мини-карты открывает квадрат 5x5 районов как мини-модель мира; клик по ячейке переносит камеру на конкретный тайл выбранного района | `frontend/src/features/world-map/MapWidget.tsx`, `frontend/src/game/coordinates/district.ts`, `frontend/src/game/state/useGameStore.ts` | 🟡 MapWidget.tsx и district helpers/test существуют; полная приёмка 5×5 и переходов камеры не выполнена |
| 3.16 | Полный редизайн UI под стиль Эолии по фазе 24: визуальная система, шрифт, HUD/inspector, отсутствие наложений, сворачиваемые чат и уведомления, сохранение UI preferences; установка стороннего скилла не является критерием готовности продукта | `frontend/src/app/styles/`, `frontend/src/features/hud/`, `frontend/src/features/chat/`, `frontend/src/features/notifications/`, `frontend/src/shared/store/`, `docs/art/visual-style-guide.md` | ⏳ |

---

## Фаза 4 — Здания, размещение и строительство

| # | Что | Файлы | Статус |
|---|---|---|---|
| 4.1 | Domain: `Building`, `BuildingType`, `Footprint`, lifecycle states (`planned`, `building`, `active`, `damaged`, `ruined`) | `backend/internal/domain/building/`, `shared/building/` | ✅ |
| 4.2 | Каталог типов зданий MVP: ратуша, землянка, деревянный/каменный дом, многоквартирный дом, вилла, дворец, жилой небоскреб, workshop, хранилище монет, market, tower, эволюция стен, road, Союзный дом | `backend/internal/domain/catalog/`, `shared/catalog/buildings.ts` | ✅ |
| 4.3 | Миграции buildings/building_jobs и индексы по owner/chunk/footprint | `backend/db/migrations/` | ✅ |
| 4.4 | SQL-запросы и Postgres-репозитории buildings/build jobs | `backend/db/query/building.sql`, `backend/internal/adapter/postgres/building_repo.go` | ✅ |
| 4.5 | Правила размещения: footprint, занятость тайлов, terrain restrictions, дороги/стены; без требования контролируемой территории | `backend/internal/domain/building/placement.go` | ✅ |
| 4.6 | `service/building`: place, cancel, complete, demolish, repair, list by chunk/player | `backend/internal/service/building.go` | ✅ |
| 4.7 | HTTP endpoints: `POST /buildings`, `GET /buildings/{id}`, `PATCH /buildings/{id}`, `DELETE /buildings/{id}` | `backend/internal/adapter/http/handler/building.go`, `backend/internal/adapter/http/dto/building.go` | ✅ |
| 4.8 | Frontend build catalog: категории, стоимость, время строительства, disabled state при нехватке ресурсов | `frontend/src/features/buildings/` | ✅ |
| 4.9 | Placement preview: допустимое/недопустимое размещение, footprint overlay, cost/time preview | `frontend/src/features/build-placement/`, `frontend/src/game/overlays/placement.ts` | ✅ |
| 4.10 | Building renderer: normal/construction/damaged/ruined sprites, anchors, sortOffset, selection outline | `frontend/src/game/renderers/buildings.ts`, `frontend/src/assets/buildings/` | ✅ |
| 4.11 | Server authoritative build flow: клиент отправляет intent, сервер валидирует и возвращает событие изменения чанка | `backend/internal/service/building.go`, `frontend/src/features/build-placement/` | ✅ |
| 4.12 | Unit-тесты placement rules, lifecycle, repository constraints и service errors | `backend/internal/domain/building/`, `backend/internal/service/building_test.go` | ✅ |
| 4.13 | Frontend tests для placement mode, preview states, catalog disabling | `frontend/src/features/build-placement/**/*.test.tsx` | ✅ |
| 4.14 | Событийное логирование строительства: place/cancel/complete/demolish/repair, invalid placement, resource shortage; поля `building_id`, `building_type`, `tile`, `player_id`, `chunk_id` | `backend/internal/service/building.go` | ✅ |
| 4.15 | Правила времени строительства и апгрейдов: материалы, монеты, свободное население, занятость строителей, остановка/повреждение стройки | `backend/internal/domain/building/build_rules.go`, `backend/internal/service/building.go`, `shared/catalog/buildings.ts` | ✅ |
| 4.16 | Лимит построек от ратуши: дороги не расходуют лимит, все остальные постройки расходуют; апгрейд ратуши повышает лимит | `backend/internal/domain/building/limits.go`, `backend/internal/domain/catalog/buildings.go`, `frontend/src/features/buildings/` | ✅ |
| 4.17 | Жилая ветка: Землянка → деревянный дом → каменный дом → ветки `многоквартирный дом/жилой небоскреб` и `вилла/дворец` | `backend/internal/domain/catalog/housing.go`, `shared/catalog/buildings.ts`, `frontend/src/assets/buildings/housing/` | ✅ |
| 4.18 | Таблицы характеристик для всех построек: уровни, прочность, время строительства, стоимость строительства/апгрейдов, население, размер, цепочки переходов и специальные параметры по категориям | `docs/buildings/**/*.md` | 🟡 таблицы и sync-runtime-tables.py существуют; актуальный `make catalog-check` прошёл с 0 обновлений runtime/XP, но ручная игровая проверка всех характеристик остаётся |
| 4.19 | Единый источник информации о постройках: вынести баланс из дублирующихся TS/Go каталогов в общий data-каталог и генерировать или валидировать `shared/catalog/buildings.ts` и `backend/internal/domain/catalog/buildings.go` из него | `data/buildings/`, `shared/catalog/buildings.ts`, `backend/internal/domain/catalog/buildings.go`, `tools/` | ✅ data-каталог и генерация/встраивание есть; после обновления реестра башни `make catalog-check` проходит: 72 типа в shared/backend/docs, Go catalog OK |
| 4.20 | Завершить переход построек на 1×1: убрать поддержку больших размеров и упоминания из клиента, инвентаризировать старые записи и безопасно перенести их с проверкой пересечений, затем проверить размещение и улучшения | `docs/status/i11-backend.md`, `frontend/src/features/buildings/`, `backend/db/` | 🟡 сервер запрещает новые большие постройки и их перемещение/улучшение; клиент и исторические записи ещё требуют работы и приёмки |

---

## Фаза 5 — Экономика, ресурсы и инвентарь

| # | Что | Файлы | Статус |
|---|---|---|---|
| 5.1 | Domain: `ResourceType`, `Inventory`, `ProductionRecipe`, `ResourceNode`, `StorageLimit` | `backend/internal/domain/economy/` | ✅ |
| 5.2 | Миграции player_inventories/resource_nodes/production_jobs/transactions | `backend/db/migrations/` | ✅ |
| 5.3 | SQL-запросы и репозитории inventory/resources/production | `backend/db/query/economy.sql`, `backend/internal/adapter/postgres/economy_repo.go` | ✅ |
| 5.4 | Каталог ресурсов и production recipes для MVP: монеты, эолийские кристаллы, большой список материалов, нефть, бензин, супер-ресурсы, добыча, переработка, хранение, потребление рабочих | `backend/internal/domain/catalog/economy.go`, `shared/catalog/resources.ts` | ✅ |
| 5.5 | `service/economy`: get inventory, reserve/spend/add resources, calculate coin capacity from хранилища монет, transaction ledger; остальные ресурсы без лимитов | `backend/internal/service/economy.go` | ✅ |
| 5.6 | `service/resource`: spawn/list/claim/harvest resource nodes, depletion/respawn | `backend/internal/service/resource.go` | ✅ |
| 5.7 | Production ticks: запуск/завершение производства, offline progress, idempotent completion | `backend/internal/service/production.go`, `backend/internal/worker/production_worker.go` | ✅ |
| 5.8 | HTTP endpoints: inventory, resource node details, harvest/start production/cancel production | `backend/internal/adapter/http/handler/economy.go`, `backend/internal/adapter/http/dto/economy.go` | ✅ |
| 5.9 | Frontend resource bar wiring: live values, coin capacity warnings, spend animations, insufficient resources feedback; остальные ресурсы без лимитов | `frontend/src/features/hud/`, `frontend/src/features/economy/` | ✅ |
| 5.10 | Resource node renderer and inspector: neutral/claimed/depleted, owner, time to respawn | `frontend/src/game/renderers/resources.ts`, `frontend/src/features/inspector/` | ✅ |
| 5.11 | Production UI: building recipes, timers, queue status, collect/complete feedback | `frontend/src/features/production/` | ✅ |
| 5.12 | Unit-тесты economy domain/service: spend/add, лимит монет, отсутствие лимитов у материалов, recipes, production timers, harvest rules | `backend/internal/domain/economy/`, `backend/internal/service/economy_test.go` | ✅ |
| 5.13 | Frontend tests для resource bar, production panel, insufficient resources states | `frontend/src/features/economy/**/*.test.tsx`, `frontend/src/features/production/**/*.test.tsx` | ✅ |
| 5.14 | Событийное логирование экономики: resource spent/added/harvested, production started/completed, coin capacity overflow | `backend/internal/service/economy.go`, `backend/internal/service/production.go` | ✅ |
| 5.15 | Нефтяные скважины: spawn/claim/harvest, лимиты, спорное владение объектом и интеграция с инвентарём; без контролируемой территории | `backend/internal/domain/economy/oil.go`, `backend/internal/service/resource.go`, `frontend/src/game/renderers/resources.ts` | ✅ |
| 5.16 | Нефтеперерабатывающий завод и бензин: рецепт `нефть -> бензин`, хранение топлива, потребление бензина заводами средних/поздних уровней | `backend/internal/domain/catalog/production.go`, `backend/internal/service/production.go`, `shared/catalog/resources.ts` | ✅ |
| 5.17 | Поля/грядки: стадии роста, сбор ресурсов и монет, шанс супер-версии 0.5-1%, супер-продукты и отдельные награды | `backend/internal/domain/economy/field.go`, `backend/internal/service/field.go`, `frontend/src/features/fields/` | ✅ |
| 5.18 | Население как рабочая сила экономики: назначение на стройку, поля, заводы, защиту, ремонт; свободные/занятые жители | `backend/internal/domain/player/population.go`, `backend/internal/service/population.go`, `frontend/src/features/population/` | ✅ |

---

## Фаза 6 — Realtime WebSocket и события мира

| # | Что | Файлы | Статус |
|---|---|---|---|
| 6.1 | WebSocket gateway: upgrade, auth, connection registry, player presence, graceful close | `backend/internal/adapter/ws/gateway.go` | ✅ |
| 6.2 | Protocol envelope: `type`, `event_id`, `seq`, `sent_at`, `chunk_id`, payload versioning | `backend/internal/adapter/ws/protocol.go`, `shared/events/` | ✅ |
| 6.3 | Subscription model: viewport/chunk subscriptions, player private channel, alliance channel placeholders | `backend/internal/adapter/ws/subscription.go` | ✅ |
| 6.4 | Event bus внутри backend: publish/subscribe для domain events без привязки к WS | `backend/internal/service/eventbus.go` | ✅ |
| 6.5 | Delta events для карты: tile changed, building placed/updated/removed, resources changed, combat event, monster event | `shared/events/world.ts`, `backend/internal/service/events.go` | ✅ |
| 6.6 | Backpressure и rate limits: bounded send queue, disconnect slow clients, command throttling | `backend/internal/adapter/ws/connection.go`, `backend/internal/adapter/ws/ratelimit.go` | ✅ |
| 6.7 | Client WS manager: reconnect, auth refresh, subscriptions by viewport, event ordering, missed-event recovery | `frontend/src/shared/realtime/`, `frontend/src/features/world/realtime.ts` | ✅ |
| 6.8 | Optimistic UI policy: только безопасные previews; authoritative server events update canonical state | `frontend/src/game/state/`, `frontend/src/features/build-placement/` | ✅ |
| 6.9 | Presence indicators: online/offline state, player cursor/selection optional для dev | `backend/internal/service/presence.go`, `frontend/src/features/presence/` | ✅ |
| 6.10 | Unit-тесты WS protocol, subscriptions, auth, backpressure, event fanout | `backend/internal/adapter/ws/` | ✅ |
| 6.11 | Frontend tests WS reconnect/subscription/update reducers | `frontend/src/shared/realtime/**/*.test.ts`, `frontend/src/features/world/**/*.test.ts` | ✅ |
| 6.12 | Логирование realtime: connect/disconnect/auth fail/subscribe/unsubscribe/dropped message/reconnect hints | `backend/internal/adapter/ws/`, `frontend/src/shared/realtime/` | ✅ |

---

## Фаза 7 — Симуляция мира, таймеры и фоновые задачи

Целевой подход: авторитетная серверная симуляция с явными тиками, очередями действий и идемпотентными обработчиками. Redis используется для временных очередей и distributed locks, PostgreSQL остаётся источником истины. Фоновые задачи не должны менять состояние мира без транзакционной фиксации в БД и публикации событий для клиентов.

В эту фазу входят только базовые процессы MVP: завершение строительства, производство ресурсов, respawn ресурсных узлов, перемещение простых монстров, decay/repair timers и доставка realtime-событий. Прямые атаки и созданные игроками монстры развиваются в фазе 10; рейды исключены. Рынок и расширенные союзные операции относятся к фазе 11.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 7.1 | Simulation config: tick interval, batch size, worker concurrency, lock TTL, catch-up limit, shutdown timeout | `backend/pkg/config/config.go`, `backend/.env.example` | ✅ |
| 7.2 | Domain action queue: `GameAction`, statuses, due_at, idempotency key, actor/target refs | `backend/internal/domain/action/`, `backend/db/migrations/` | ✅ |
| 7.3 | PostgreSQL action repository: append/fetch due with lock/skip locked/mark done/mark failed/retry | `backend/db/query/action.sql`, `backend/internal/adapter/postgres/action_repo.go` | ✅ |
| 7.4 | Transaction boundary для симуляции: unit of work, atomic state update + event append | `backend/internal/service/ports.go`, `backend/internal/adapter/postgres/uow.go` | ✅ |
| 7.5 | Simulation worker lifecycle: start/stop, leader lock, tick metrics, panic recovery | `backend/internal/worker/simulation/`, `backend/cmd/worker/` | ✅ |
| 7.6 | Завершение строительства по таймеру: activate building, update chunk version, publish event | `backend/internal/worker/simulation/building.go` | ✅ |
| 7.7 | Production tick: calculate finished production jobs, add resources with capacity handling, publish deltas | `backend/internal/worker/simulation/production.go` | ✅ |
| 7.8 | Resource respawn/depletion tick: restore nodes, spawn limited neutral nodes around active areas | `backend/internal/worker/simulation/resources.go` | ✅ |
| 7.9 | Basic offline progress: bounded catch-up при login/load player state | `backend/internal/service/economy.go`, `backend/internal/service/player.go` | ✅ |
| 7.10 | Outbox events для надёжной доставки realtime/email/future notifications | `backend/db/migrations/`, `backend/internal/domain/event/`, `backend/internal/adapter/postgres/outbox_repo.go` | ✅ |
| 7.11 | Dispatcher outbox → WS/event bus: retry, dead-letter, idempotent event ids | `backend/internal/worker/outbox_dispatcher.go` | ✅ |
| 7.12 | Unit-тесты simulation ticks, locking, idempotency, retries и event publication | `backend/internal/worker/simulation/**/*_test.go`, `backend/internal/service/action_test.go` | ✅ |
| 7.13 | Логирование simulation/outbox: tick start/success/failure, slow tick, action result, retry/dead-letter | `backend/internal/worker/`, `backend/internal/service/` | ✅ |
| 7.14 | Tick полей и грядок: рост по стадиям, готовность урожая, супер-версия, начисление ресурсов и монет | `backend/internal/worker/simulation/fields.go`, `backend/internal/service/field.go` | ✅ |
| 7.15 | Tick топлива: потребление бензина активными заводами, остановка/замедление при нехватке, offline catch-up | `backend/internal/worker/simulation/production.go`, `backend/internal/domain/economy/fuel.go` | ✅ |
| 7.16 | Tick нефтяных скважин: добыча нефти, contested ownership, depletion/respawn или rate limiting добычи | `backend/internal/worker/simulation/oil.go`, `backend/internal/service/resource.go` | ✅ |

---

## Фаза 8 — Монстры, PvE и угрозы

| # | Что | Файлы | Статус |
|---|---|---|---|
| 8.1 | Domain: `Monster`, `MonsterType`, `Threat`, `MovementIntent`, базовые AI states | `backend/internal/domain/monster/` | ✅ |
| 8.2 | Миграции monsters/monster_spawn_points/monster_events | `backend/db/migrations/` | ✅ |
| 8.3 | SQL-запросы и репозитории monsters/spawns | `backend/db/query/monster.sql`, `backend/internal/adapter/postgres/monster_repo.go` | ✅ |
| 8.4 | Каталог монстров MVP: roaming melee, resource guardian, ruins guardian с параметрами hp/damage/speed/aggro | `backend/internal/domain/catalog/monsters.go`, `shared/catalog/monsters.ts` | ✅ |
| 8.5 | AI movement tick: wandering, aggro radius, path constraints, chunk transitions | `backend/internal/worker/simulation/monster_ai.go` | ✅ |
| 8.6 | PvE combat rules: attack building/player unit placeholder, damage, death, loot/reward, cooldown | `backend/internal/domain/combat/`, `backend/internal/service/combat.go` | ✅ |
| 8.7 | Threat service: calculate danger around player territory, notify clients, inspector status | `backend/internal/service/threat.go` | ✅ |
| 8.8 | HTTP endpoints: list monsters in viewport, monster details, attack/defend action | `backend/internal/adapter/http/handler/monster.go`, `backend/internal/adapter/http/dto/monster.go` | ✅ |
| 8.9 | Frontend monster renderer: sprite states, health bars, aggro/target overlay, movement interpolation | `frontend/src/game/renderers/monsters.ts`, `frontend/src/features/monster/` | ✅ |
| 8.10 | Inspector states для выбранного монстра и угрозы рядом с постройками | `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/threat/` | ✅ |
| 8.11 | Realtime monster events: moved/attacked/damaged/died/spawned/despawned | `shared/events/monster.ts`, `frontend/src/features/world/realtime.ts` | ✅ |
| 8.12 | Unit-тесты AI movement, aggro, combat calculations, loot, threat service | `backend/internal/domain/monster/`, `backend/internal/domain/combat/` | ✅ |
| 8.13 | Frontend tests monster rendering state reducers and inspector actions | `frontend/src/game/renderers/monsters.test.ts`, `frontend/src/features/inspector/Inspector.test.tsx` | ✅ |
| 8.14 | Событийное логирование PvE: spawn/move/aggro/attack/damage/death/reward; поля `monster_id`, `monster_type`, `target_id`, `chunk_id` | `backend/internal/service/combat.go`, `backend/internal/worker/simulation/monster_ai.go` | ✅ |
| 8.15 | Реализовать серверное обнаружение монстров сторожевой башней, создание и доставку тревоги владельцу; проверить радиус, жизненный цикл башни и события симуляции | `docs/status/tower-c7.md`, `backend/internal/worker/simulation/`, `frontend/src/features/notifications/` | 🟡 уровни башни и голубая граница проектного радиуса подключены; серверное обнаружение и тревога отсутствуют |

---

## Фаза 9 — Территория, владение и защита

Статус: исключена из текущего направления. Контролируемая территория удалена из активной логики: игроки могут строить на любой свободной допустимой клетке без требования владения/влияния.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 9.1 | Domain: `Territory`, `Claim`, `ProtectionZone`, `Border`, `Influence` | `backend/internal/domain/territory/` | 🚫 |
| 9.2 | Миграции territory_claims/protection_zones/border_events | `backend/db/migrations/` | 🚫 |
| 9.3 | SQL-запросы и репозитории territory/protection | `backend/db/query/territory.sql`, `backend/internal/adapter/postgres/territory_repo.go` | 🚫 |
| 9.4 | Правила влияния построек: city center, roads, towers, walls, contested zones | `backend/internal/domain/territory/territory.go` | 🚫 |
| 9.5 | `service/territory`: recalculate claims, get owner/protection for tile, validate expansion | `backend/internal/service/territory.go` | 🚫 |
| 9.6 | Интеграция placement rules с территорией: запрет/стоимость/риск строительства вне влияния | `backend/internal/service/building.go`, `backend/internal/service/territory.go` | 🚫 |
| 9.7 | Defense service: tower coverage, wall blocking, protected/offline status, vulnerability windows | `backend/internal/service/defense.go`, `backend/internal/domain/territory/territory.go` | 🚫 |
| 9.8 | HTTP endpoints: territory by viewport, tile ownership/protection, player borders | `backend/internal/adapter/http/handler/territory.go`, `backend/internal/adapter/http/dto/territory.go` | 🚫 |
| 9.9 | Frontend territory overlay: owner colors, contested/protected/danger states, opacity controls | `frontend/src/game/overlays/territory.ts`, `frontend/src/features/territory/` | 🚫 |
| 9.10 | Inspector ownership blocks: owner, protection, contest status, allowed actions | `frontend/src/features/inspector/` | 🚫 |
| 9.11 | Realtime territory events: claimed/lost/contested/protection changed | `shared/events/territory.ts`, `frontend/src/features/world/realtime.ts` | 🚫 |
| 9.12 | Unit-тесты territory rules, protection calculations, placement integration | `backend/internal/domain/territory/territory_test.go`, `backend/internal/service/territory_test.go` | 🚫 |
| 9.13 | Событийное логирование территории: claim/recalculate/protection changed/contested, invalid expansion | `backend/internal/service/territory.go`, `backend/internal/service/defense.go` | 🚫 |

---

## Фаза 10 — Прямые PvP-атаки, созданные монстры, разрушения и ремонт

| # | Что | Файлы | Статус |
|---|---|---|---|
| 10.1 | Domain прямого PvP: intent применения инвентарного оружия/бомб, отложенный взрыв, создание игроком монстра, DamageEvent и cooldown; рейды исключены | `backend/internal/domain/action/`, `backend/internal/domain/combat/`, `backend/internal/domain/monster/` | 🟡 action/combat/monster модели реализованы; приёмка полного прямого PvP остаётся |
| 10.2 | Миграции и хранение прямого PvP: действия оружия, создатель/срок жизни монстра, привязка цели и cooldown; отдельной таблицы raids не требуется | `backend/db/migrations/000040_direct_pvp.sql` | 🟡 000040_direct_pvp.sql существует в рабочем дереве; применение к БД в этом аудите не проверено |
| 10.3 | Репозитории действий, условного урона постройке и созданных монстров; конкурентные проверки и согласованная запись результата | `backend/internal/adapter/postgres/action_repo.go`, `backend/internal/adapter/postgres/building_repo.go`, `backend/internal/adapter/postgres/monster_repo.go` | 🟡 DamageIfCurrent и action/monster repositories есть; транзакционные гонки требуют прогона |
| 10.4 | Правила прямой атаки: чужая допустимая цель, дальность через шов мира, стоимость оружия, задержка взрыва, cooldown и повторная проверка владельца/состояния цели; отдельно определить защиту от чрезмерных потерь | `backend/internal/service/pvp.go`, `backend/internal/service/combat.go`, `data/balance/v2.json` | 🟡 правила атаки, офлайн-защита и суточный бюджет PvP-потерь реализованы для оружия и созданных монстров; миграция 000050 и балансировочная/SQL приёмка остаются |
| 10.5 | CombatService: применение оружия к постройке, постановка/исполнение взрыва и создание монстра за ресурсы; без путешествия, отмены рейда и рейдовой добычи | `backend/internal/service/pvp.go`, `backend/internal/service/combat.go`, `backend/internal/worker/simulation/runner.go` | 🟡 pvp.go и UseBuildingWeapon реализованы; текущий backend-прогон недоступен без Go |
| 10.6 | Ремонт: владение и допустимое состояние, стоимость, рабочие, таймер, атомарная оплата/завершение и правила восстановления руин | `backend/internal/service/repair.go`, `backend/db/migrations/000042_repair_jobs.sql`, `backend/internal/adapter/postgres/repair_repo.go`, `frontend/src/features/inspector/Inspector.tsx` | 🟡 платный таймерный ремонт реализован: quote/status API, SQL queue, резерв рабочего, завершение worker и возврат при утрате цели; тесты добавлены, Go/БД прогон недоступен |
| 10.7 | HTTP прямого PvP: POST /buildings/{id}/weapons, POST /combat/monsters, GET /combat/rules и PATCH /buildings/{id} с action=repair; без /raids | `backend/internal/adapter/http/handler/combat.go`, `backend/internal/adapter/http/handler/building.go`, `backend/internal/adapter/http/router.go` | 🟡 routes/CombatHandler и repair action есть; текущая проверка API/БД не выполнена |
| 10.8 | Frontend прямой атаки из инспектора: выбор инвентарного оружия/бомбы или создания монстра, цена/дальность/cooldown, подтверждение и причины запрета | `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/shared/api/monsters.ts` | 🟡 действия есть в Inspector.tsx; отдельная приёмка запретов/ожидания/cooldown нужна |
| 10.9 | Визуальный результат прямой атаки и PvE: урон, попадание/взрыв, повреждение/разрушение постройки и обновление карты | `frontend/src/game/renderer/objectLayer/`, `frontend/src/features/world/realtime.ts`, `frontend/src/features/world/combatAudio.ts` | 🟡 события урона, damaged/ruined и combatAudio есть; полный набор визуальных эффектов не подтверждён |
| 10.10 | Инспектор и журнал прямого PvP: отложенные взрывы, созданные монстры, cooldown и результат; уведомления атакующего и владельца цели | `frontend/src/features/inspector/`, `frontend/src/features/event-log/`, `frontend/src/features/notifications/` | 🟡 realtime обновляет постройки/монстров; полный журнал взрывов/cooldown и адресные уведомления не завершены |
| 10.11 | Защита прямого PvP от злоупотреблений: rate limits, cooldown, идемпотентность, смена владельца цели, конкурентное списание; определить и проверить политику offline/предела потерь | `backend/internal/service/pvp.go`, `backend/internal/service/combat.go`, `backend/internal/adapter/http/middleware/` | 🟡 cooldown/idempotency и повторная проверка владельца есть; политика offline/предела потерь не подтверждена |
| 10.12 | Backend-тесты прямого PvP и ремонта: повтор команды, конкурентная атака, смена владельца, граница мира, отложенный взрыв, срок жизни монстра и ограничения потерь | `backend/internal/service/pvp_test.go`, `backend/internal/worker/simulation/pvp_monster_test.go`, `backend/internal/adapter/http/pvp_routes_test.go` | 🟡 pvp_test.go, pvp_monster_test.go и pvp_routes_test.go есть; весь целевой набор и запуск не подтверждены |
| 10.13 | Frontend-тесты оружия/создания монстра, недопустимых целей, ожидания ответа и уведомлений владельца | `frontend/src/features/inspector/Inspector.test.tsx`, `frontend/src/game/IsoMap.interaction.test.tsx` | 🟡 Inspector/ToolBar/IsoMap тесты есть; полный сценарий прямой атаки и уведомления не покрыт |
| 10.14 | Событийное логирование прямого PvP: применение оружия, взрыв, создание монстра, damage/repair, forbidden target и cooldown denial | `backend/internal/service/pvp.go`, `backend/internal/service/combat.go`, `backend/internal/service/building.go` | 🟡 combat.building.damaged и логи ремонта есть; полнота событий отказов/создания/взрыва требует сверки |

---

## Фаза 11 — Союзы, чат, рынок и социальные механики

| # | Что | Файлы | Статус |
|---|---|---|---|
| 11.1 | Domain alliances: `Alliance`, `AllianceMembership`, роли `leader/deputy/officer/member`, назначение казначея одному заместителю, invites, permissions | `backend/internal/domain/alliance/` | ✅ |
| 11.2 | Миграции alliances/alliance_members/alliance_invites/alliance_treasury/alliance_buffs/chat_messages/market_orders | `backend/db/migrations/` | ✅ |
| 11.3 | SQL-запросы и репозитории alliances/treasury/buffs/chat/market | `backend/internal/adapter/postgres/social_repo.go`, `backend/db/migrations/000011_social.sql`, `backend/cmd/api/app.go` | 🟡 PostgreSQL SocialRepo реализован и выбирается при наличии БД; изолированные SQL/Redis интеграционные тесты ранее прошли, но актуальный полный многопользовательский сценарий требует приёмки |
| 11.4 | `service/alliance`: create via Союзный дом, invite, accept/decline, roles, deputy limit 2, treasurer assignment, leave/kick, profile | `backend/internal/service/alliance.go`, `backend/internal/adapter/http/handler/social.go`, `frontend/src/features/alliance/AlliancePanel.tsx` | 🟡 leave/kick/передача лидерства/роспуск последним лидером реализованы в сервисе/API/UI с иерархией и блокировкой союза; серверный Go-прогон ранее прошёл, SQL/live права и гонки требуют приёмки |
| 11.5 | Союзная помощь для руин, нефтяных скважин и защиты как MVP placeholders; не создаёт контроль территории | `backend/internal/service/alliance.go`, `backend/internal/domain/alliance/` | ✅ |
| 11.6 | Chat service: global/nearby/alliance/private channels, moderation flags, pagination | `backend/internal/service/chat.go` | 🟡 каналы, limit и moderation flag есть; nearby-фильтрация по расстоянию и cursor pagination требуют реализации |
| 11.7 | Market service MVP: create buy/sell order, cancel, match simple resource trades, fees | `backend/internal/service/market.go`, `backend/internal/domain/market/` | 🟡 авто-match с частичным исполнением, price/time priority, escrow/refund, fees и приватными событиями реализован; SQL/race прогон остаётся |
| 11.8 | HTTP endpoints alliances/chat/market | `backend/internal/adapter/http/handler/alliance.go`, `backend/internal/adapter/http/handler/chat.go`, `backend/internal/adapter/http/handler/market.go` | ✅ |
| 11.9 | Realtime chat and alliance events | `shared/events/chat.ts`, `shared/events/alliance.ts`, `backend/internal/service/chat.go`, `backend/internal/service/alliance.go`, `frontend/src/features/world/realtime.ts` | 🟡 ChatService/AllianceService публикуют события после commit, private fanout выбирает текущих участников; shared union/client invalidation/reconnect готовы; реальный WS сценарий подготовлен, но не пройден |
| 11.10 | Frontend alliance panel: membership, invites, roles, treasurer, Союзный дом, казна, баффы, статус союза | `frontend/src/features/alliance/` | 🟡 MVP |
| 11.11 | Frontend chat UI: channels, unread, moderation-safe rendering, reconnect handling | `frontend/src/features/chat/`, `backend/internal/service/chat.go`, `backend/db/migrations/000041_chat_reads.sql` | 🟡 серверные monotonic read cursors со scope союза, unread API, UI счётчики и resync реализованы; frontend-тест проходит; миграция 000041/SQL приёмка ещё не выполнены |
| 11.12 | Frontend market UI: orders list, create/cancel, inventory impact preview | `frontend/src/features/market/` | 🟡 в панели союза |
| 11.13 | Unit-тесты alliance/chat/market services and permissions | `backend/internal/service/alliance_test.go`, `backend/internal/service/chat_test.go`, `backend/internal/service/market_test.go` | ✅ |
| 11.14 | Событийное логирование social: alliance create/invite/role/treasury/buff, chat moderation events, market order lifecycle | `backend/internal/service/alliance.go`, `backend/internal/service/chat.go`, `backend/internal/service/market.go` | ✅ |
| 11.15 | Союзный дом как постройка: уровни, лимит участников, открытие офицеров/казначея/баффов, синхронизация с каталогом зданий | `backend/internal/domain/catalog/alliance_buildings.go`, `backend/internal/service/alliance.go`, `frontend/src/features/buildings/` | ✅ |
| 11.16 | Союзная казна: пожертвования ресурсов, права расходования лидером/казначеем, ledger пожертвований и расходов | `backend/internal/domain/alliance/treasury.go`, `backend/internal/service/alliance_treasury.go`, `frontend/src/features/alliance/TreasuryPanel.tsx` | 🟡 полный баланс ledger, транзакционные расходы лидером/казначеем, проверка получателя и UI реализованы; SQL/live приёмка остаётся |
| 11.17 | Союзные баффы: покупка/апгрейд за казну, бонусы строительства/ремонта/добычи/обороны/руин/бензина с caps | `backend/internal/domain/alliance/buffs.go`, `backend/internal/service/alliance_buffs.go`, `shared/catalog/alliance-buffs.ts` | 🟡 платные build/repair/harvest/defense buffs из общего каталога, max level 5 и caps; дополнительные эффекты и серверная приёмка остаются |

| 11.18 | Атомарные операции рынка: резерв ресурсов и запись заявки в одной транзакции; отмена и возврат ровно один раз при гонке/сбое; интеграционные тесты | `backend/internal/service/market.go`, `backend/internal/service/ports.go`, `backend/internal/adapter/postgres/` | 🟡 UnitOfWork + row/advisory locks, reserve/order и cancel/refund атомарны в коде; изолированные SQL/Redis тесты ранее прошли, но актуальные rollback/race и live сценарии рынка остаются |

---

## Фаза 12 — Middleware, роутер, Swagger и API-контракт

| # | Что | Файлы | Статус |
|---|---|---|---|
| 12.1 | Middleware CORS, request id, recoverer, body limit, timeout | `backend/internal/adapter/http/middleware/` | ✅ |
| 12.2 | Middleware logger production access log: route pattern, status class, response size, panic marker | `backend/internal/adapter/http/middleware/logger.go` | ✅ |
| 12.3 | Rate limiting по risky routes: auth, build/weapon/summon, chat, market, uploads, WS commands | `backend/internal/adapter/http/middleware/ratelimit.go`, `backend/internal/adapter/ws/ratelimit.go` | ✅ |
| 12.4 | Idempotency keys для небезопасных POST: building placement, применение оружия/создание монстра, market order, alliance invite | `backend/internal/adapter/http/middleware/idempotency.go`, `backend/internal/adapter/postgres/idempotency_store.go`, `backend/db/migrations/000036_idempotency_reservations.sql`, `frontend/src/shared/api/client.ts` | ✅ ключи согласованы на клиенте и сервере для строительства, оружия, создания монстра, рынка, приглашений и расхода казны; fingerprint включает query/body/Content-Type; middleware и PostgreSQL покрыты тестами |
| 12.5 | Сборка router с группами `/api/v1/auth`, `/players`, `/world`, `/buildings`, `/economy`, `/monsters`, `/alliances`, `/chat`, `/market`, `/admin`, `/health`, `/metrics`, `/swagger` | `backend/internal/adapter/http/router.go` | ✅ группы маршрутов, health/readiness, metrics, Swagger и WS endpoint собраны; контрактный smoke проверяет, что каждая OpenAPI-операция смонтирована |
| 12.6 | Swagger/OpenAPI annotations и генерация контракта | `backend/internal/adapter/http/openapi.go`, `backend/cmd/openapi-gen/`, `backend/docs/swagger/openapi.json` | ✅ генератор `cd backend && go run ./cmd/openapi-gen` синхронизирует snapshot; freshness-тест сравнивает весь runtime контракт, включая security, параметры путей, системные маршруты и Idempotency-Key |
| 12.7 | Typed frontend API client из OpenAPI или ручной client с contract tests | `frontend/src/shared/api/`, `shared/api/` | ✅ |
| 12.8 | API compatibility policy: versioning, error shape, pagination, cursor rules, deprecation notes | `docs/architecture/api.md`, `backend/internal/adapter/http/dto/` | ✅ |
| 12.9 | Unit-тесты middleware/router smoke/OpenAPI freshness | `backend/internal/adapter/http/middleware/`, `backend/internal/adapter/http/router_test.go` | ✅ |

---

## Фаза 13 — Администрирование и модерация

| # | Что | Файлы | Статус |
|---|---|---|---|
| 13.1 | Domain admin/audit: admin roles, audit actions, moderation actions | `backend/internal/domain/player/administration.go` | 🟡 роли и AccountAudit с предыдущим/новым состоянием реализованы в domain/player; полная модель модерации остаётся |
| 13.2 | Миграции admin_audit_log/moderation_events/system_settings | `backend/db/migrations/` | 🟡 миграция 000049_account_admin.sql добавляет аудит аккаунтов; применение и полный контур moderation/system settings остаются |
| 13.3 | `service/admin`: list players, get player, deactivate/activate, set admin, force logout | `backend/internal/service/admin.go` | 🟡 блокировка/разблокировка, смена ролей, защита последнего активного admin и отзыв сессий реализованы; SQL/серверная приёмка остаётся |
| 13.4 | Admin world overview: chunks, buildings, resources, monsters, отложенные атаки, online players | `backend/internal/service/admin_world.go` | ⏳ |
| 13.5 | Moderation: delete chat message, freeze player, resolve abuse report placeholder | `backend/internal/service/moderation.go` | ⏳ |
| 13.6 | System diagnostics: PostgreSQL, Redis, WS gateway, worker status, tick lag, app version/uptime | `backend/internal/service/diagnostics.go` | ⏳ |
| 13.7 | HTTP endpoints admin users/world/moderation/diagnostics/audit | `backend/internal/adapter/http/handler/admin.go` | 🟡 admin routes, PATCH /admin/players/{id} и GET /admin/accounts/audit реализованы; весь диагностический контур и серверная приёмка остаются |
| 13.8 | Frontend admin panel: player list, player detail, system status, world debug controls | `frontend/src/features/admin/` | 🟡 панель аккаунтов/ролей/причины и аудит реализованы; три клиентских теста проходят, полные диагностические экраны остаются |
| 13.9 | Persistent audit logging admin actions без PII/секретов и read-only audit API | `backend/internal/adapter/postgres/admin_accounts.go`, `backend/internal/service/admin_accounts.go` | 🟡 аудит смены статуса/роли сохраняется транзакционно в PostgreSQL и доступен через read-only API; SQL-проверка не выполнена |
| 13.10 | Unit-тесты admin permissions, audit persistence, moderation safety | `backend/internal/service/admin_test.go`, `frontend/src/features/admin/**/*.test.tsx` | 🟡 добавлены Go-тесты прав, последнего администратора, отзыва HTTP/WS и SQL-сохранности; они не запущены; три клиентских теста панели проходят |

---

## Фаза 14 — Ассеты, визуальный пайплайн и контент

| # | Что | Файлы | Статус |
|---|---|---|---|
| 14.1 | Формат visual definitions: atlas/frame/footprint/anchor/sortOffset/states/shadow | `shared/assets/visual-def.ts`, `frontend/src/assets/manifest.json` | 🟡 RuntimeAssetManifest/assetManifestTypes.ts и visual-spec schema есть; единое покрытие всех объектов не завершено |
| 14.2 | Каталог placeholder-ассетов MVP без копирования чужого IP: terrain, крупные тайлы, resources, oil wells, buildings, ruins, monsters, effects | `frontend/src/assets/`, `docs/art/asset-guidelines.md` | 🟡 public/assets содержит terrain/resources/buildings/monsters; полное покрытие/приёмка остаются |
| 14.3 | Blender export convention: фиксированная камера, размеры, naming, states, shadows | `docs/art/blender-pipeline.md`, `tools/assets/` | 🟡 building-asset-contract.md и Blender tools есть; единое применение контракта ко всем семействам ещё нужно |
| 14.4 | Texture atlas build: packing sprites, JSON metadata generation, cache busting | `tools/assets/atlas/`, `frontend/src/assets/atlases/` | 🟡 atlas loader и animation fixtures есть; массовая production-упаковка/версионирование всех спрайтов не подтверждены |
| 14.5 | Asset validation script: missing frames, footprint mismatch, duplicate ids, oversized textures | `tools/assets/validate-assets.ts` или `scripts/validate_assets.go` | 🟡 validate_asset_specs/manifests/sprites/lods/ground существуют; единый полный успешный прогон не выполнен |
| 14.6 | Runtime asset loader: Pixi assets init, loading progress, fallback sprites, error reporting | `frontend/src/game/assets/` | 🟡 Pixi Assets, objectTextureCache и fallback реализованы; общий progress/unload/error pipeline не завершён |
| 14.7 | Content balance files: building costs, resource rates, monster stats, cooldown оружия/создания монстра | `shared/balance/`, `backend/internal/domain/catalog/` | 🟡 баланс v2 загружается из JSON; актуальный `make catalog-check` проходит, но баланс монстров и оружия требует игровой приёмки |
| 14.8 | Internal content viewer: inspect sprites, anchors, footprints, states and sort order | `frontend/src/features/assets/AssetDebugPanel.tsx` | 🟡 AssetDebugPanel и Three BuildingModelPreview есть; полный viewer всех состояний/якорей не подтверждён |
| 14.9 | Tests/validation для asset manifests and balance schema | `frontend/src/game/assets/**/*.test.ts`, `shared/**/*.test.ts` | 🟡 frontend manifest/registry/LOD/texture тесты проходят; полная проверка схем и внешних ассетов остаётся |
| 14.10 | Документ IP boundaries: нельзя использовать gnomgrad names/images/texts, правила placeholder и финального контента | `docs/art/ip-boundaries.md`, `AGENTS.md` | 🟡 правила есть в AGENTS.md; отдельный документ происхождения/прав для всего production-контента не завершён |
| 14.11 | Модели уровней построек: отдельный visual для каждого уровня и апгрейда, включая жилье, ратушу, Союзный дом, заводы, дороги, поля/грядки, руины | `frontend/src/assets/buildings/`, `frontend/src/assets/manifest.json`, `docs/art/asset-guidelines.md` | 🟡 дороги всех трёх видов и состояний (`d708b59`) и башня L1–L6 в четырёх состояниях (`51c05a0`) подключены; все остальные типы/уровни/состояния не покрыты, см. фазу 22 |
| 14.12 | Ассеты нефтяной цепочки: нефтяная скважина, нефть, бензин, Нефтеперерабатывающий завод, fuel indicators без мрачной индустриальности | `frontend/src/assets/resources/`, `frontend/src/assets/buildings/industry/` | 🟡 oil_well/oil_refinery и ресурсные иконки существуют; итоговая визуальная приёмка цепочки не выполнена |
| 14.13 | Ассеты эолийских кристаллов: вытянутые тонкие шестиугольные аметистовые кристаллы для UI, карты и магазина | `frontend/src/assets/resources/aeolian-crystals/`, `frontend/src/features/hud/` | 🟡 ресурсные ассеты и HUD есть; полное покрытие карты/UI и визуальная приёмка не подтверждены |

---

## Фаза 15 — Кэширование, производительность и масштабирование

| # | Что | Файлы | Статус |
|---|---|---|---|
| 15.1 | Redis cache для chunk snapshots, player state summaries, catalog/balance, оверлеи объектов/угроз | `backend/internal/adapter/redis/game_cache.go` | 🟡 Redis TTL-кэш одиночных chunk snapshots подключён в API с возвратом к SQL при отказе; summaries, каталог и оверлеи ещё не кэшируются |
| 15.2 | Инвалидация кэша при изменении зданий/ресурсов/боёв | `backend/internal/service/cache_keys.go`, `backend/internal/service/events.go` | 🟡 события тайлов, зданий, ресурсов и монстров удаляют ключ чанка через WS-шлюз; расширение на будущие кэши и проверка гонок с записью остаются |
| 15.3 | Spatial query optimization: chunk indexes, bounding boxes, hot viewport queries | `backend/db/migrations/`, `backend/db/query/world.sql` | 🟡 добавлен частичный индекс живых монстров для viewport; SQL-план и выигрыш под нагрузкой ещё не измерены |
| 15.4 | Frontend render performance: sprite pooling, culling, batched updates, texture atlas usage, крупные тайлы без лишней overdraw | `frontend/src/game/renderers/`, `frontend/src/game/performance/` | 🟡 canvas object layers, visibility helpers и texture cache есть; убрано выделение массива на каждый кадр в счётчике FPS; pooling/атласы и измерения всех сценариев не завершены |
| 15.5 | Network performance: event coalescing, viewport diff compression, heartbeat tuning | `backend/internal/adapter/ws/`, `frontend/src/shared/realtime/` | 🟡 ping, backpressure и subscriptions есть; coalescing событий добавлен (`0a19b01`), но viewport diff compression и нагрузочные замеры остаются |
| 15.6 | Load tests: chunk load, WS fanout, placement commands, simulation ticks, chat throughput | `tests/k6/`, `tests/ws-load/` | 🟡 добавлены k6-сценарии чтения чанков/viewport, WS, размещения, чата и мониторинга тиков; k6 отсутствует в окружении, поэтому новые сценарии ещё не прогнаны |
| 15.7 | Profiling hooks: pprof in non-public admin/internal route, frontend performance marks | `backend/cmd/api/`, `frontend/src/game/performance/marks.ts` | ✅ pprof включается через PPROF_ADDR на отдельном loopback listener; браузер измеряет время до готовности карты через Performance API |
| 15.8 | Graceful degradation: Redis unavailable, WS reconnect storms, slow DB, asset load failure | `backend/internal/service/`, `frontend/src/app/` | 🟡 Redis outage покрыт SQL fallback и тестом, запрос к кэшу ограничен 500 мс; slow DB возвращает ограниченный по времени ответ, повтор WS ограничен и проверен, asset retry проверен; общий soak ещё нужен |
| 15.9 | Unit/integration tests cache-aside, invalidation, degraded fallback | `backend/internal/adapter/redis/`, `backend/internal/service/cache_test.go` | ✅ cache-aside, инвалидация и Redis fallback покрыты unit-тестами; Redis GET/SET/DEL проверяются контейнерным тестом при TEST_CONTAINERS=1 |
| 15.10 | Логирование performance/cache: hit/miss/set/delete, slow queries, slow ticks, dropped events, FPS/runtime warnings | `backend/internal/adapter/redis/`, `backend/internal/worker/`, `frontend/src/game/performance/` | 🟡 добавлены события cache hit/miss/set/delete/failure, предупреждение о медленной загрузке чанка и dev FPS warning; SQL/tick/WS метрики уже есть, пороги в нагрузке требуют проверки |
| 15.11 | Срочная оптимизация карты: найден и исправлен bottleneck DOM-отрисовки тысяч тайлов, terrain перенесён в Pixi canvas, React оставлен для UI/оверлеев | `frontend/src/game/IsoMap.tsx`, `frontend/src/game/renderer/PixiStage.tsx`, `frontend/src/features/world/useVisibleChunks.ts` | ✅ |
| 15.12 | Incremental rendering: не перерисовывать всю карту при каждом изменении, dirty chunks/tiles, partial updates и стабильные display objects | `frontend/src/game/renderers/`, `frontend/src/features/world/realtime.ts` | 🟡 есть отдельные object layers и обновления display objects; полная dirty-chunk стратегия и замеры не завершены |
| 15.13 | Data loading optimization: минимальный payload viewport, cursor/version diff, сжатие больших списков объектов, lazy details для inspector | `backend/internal/adapter/http/handler/world.go`, `backend/internal/service/world.go`, `frontend/src/shared/api/world.ts` | ⏳ |
| 15.14 | Performance tests для цикличной крупнотайловой карты: pan через границу мира, zoom, загрузка швов, 60s scroll soak | `frontend/tests/performance/map.spec.ts`, `backend/internal/service/world_wrap_test.go` | ⏳ |

---

## Фаза 16 — Тестирование и качество

| # | Что | Файлы | Статус |
|---|---|---|---|
| 16.1 | Backend unit-тесты всех доменных правил: placement, economy, combat, AI, cooldowns | `backend/internal/domain/**/*_test.go` | 🟡 доменные тесты и исторический полный Go-прогон есть; новые правила монстров и полный набор PvP/anti-abuse после изменений требуют повторной проверки |
| 16.2 | Backend service unit-тесты с fake repositories/cache/event bus | `backend/internal/service/**/*_test.go` | 🟡 добавлены матрицы построек/апгрейдов/обороны, PvP-защита и rollback/concurrency-тесты производства; исторический Go-прогон есть, текущие изменения и SQL-гонки требуют приёмки |
| 16.3 | Интеграционные тесты PostgreSQL/Redis через testcontainers-go: миграции, репозитории, locks, constraints | `backend/internal/adapter/postgres/testcontainers_integration_test.go`, `backend/internal/adapter/redis/integration_test.go` | 🟡 изолированная схема 1→53, SQL-тесты рынка/союза/отзыва/идемпотентности и Redis прошли; отдельный testcontainers-go и полный набор конкурентных constraints ещё не запускались |
| 16.4 | API smoke/e2e compose tests: auth → world → build → economy → realtime → monster → прямое PvP | `tests/e2e/api/`, `backend/internal/service/pvp.go` | 🟡 живой smoke и gameplay_restart прошли с сохранением БД; браузерный и полный многопользовательский маршрут остаются |
| 16.5 | Frontend unit/component tests для stores, panels, render state reducers, API client | `frontend/src/**/*.test.ts`, `frontend/src/**/*.test.tsx` | ✅ исторический полный frontend-прогон: 370/370 тестов в 94 файлах, проверка типов и production-сборка успешны; текущие внешние UI-правки этим прогоном не проверены |
| 16.6 | Playwright E2E playable MVP: login, load map, place building, wait completion, harvest resource, receive WS event | `frontend/tests/e2e/` | 🟡 обнаруживаются четыре live desktop/mobile сценария, включая XP/производство/рынок/чат/PvP/reconnect; запуск остановлен Vite EPERM, фактической приёмки нет |
| 16.7 | Visual regression/screenshot tests: desktop/mobile, placement, inspector states, combat/monster overlays | `frontend/tests/visual/` | ⏳ |
| 16.8 | Static quality gates: eslint, prettier, typecheck, gofmt, go vet, golangci-lint, dependency audit | `frontend/package.json`, `backend/Makefile`, `.github/workflows/ci.yml` | 🟡 TS/build, Vitest и тематические CI есть; eslint/prettier/Go quality gates и dependency audit не объединены |
| 16.9 | Manual QA checklist для playable MVP и регрессий realtime | `docs/qa/mvp-manual-acceptance.md` | 🟡 таблица есть и отделяет автоматические свидетельства; ручной desktop/mobile-прогон не выполнен |

| 16.10 | Устранить текущую регрессию objectDrawData.test.ts: согласовать ожидаемый URL ратуши с версионируемым manifest, сохранив проверку выбора текстуры; получить зелёный полный Vitest | `frontend/src/game/renderer/objectLayer/objectDrawData.test.ts`, `frontend/src/game/renderers/buildingAssetManifests.ts` | ✅ ожидание URL ратуши актуализировано; objectDrawData и полный Vitest проходят |

---

## Фаза 17 — Observability

Контур Prometheus/Grafana и его проверки подробно описаны в [отдельном плане наблюдаемости](observability-plan.md). Локальные серверные измерения и оставшиеся браузерные прогоны зафиксированы в [базовой линии](../performance/observability-baseline.md). Пункты ниже шире этого контура: игровые метрики, Redis и клиентские ошибки остаются отдельными задачами общего плана.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 17.1 | Middleware metrics: Prometheus `/metrics`, HTTP latency, WS connections, commands, errors, in-flight requests | `backend/internal/adapter/http/middleware/metrics.go`, `backend/internal/adapter/ws/metrics.go` | ✅ HTTP histogram/in-flight и WS metrics реализованы; observability-plan.md, middleware/metrics.go и ws/metrics.go |
| 17.2 | Simulation metrics: tick duration, actions processed, queue lag, lock contention, failed ticks | `backend/internal/observability/simulation.go`, `backend/internal/observability/queues.go`, `backend/internal/worker/simulation/runner.go` | ✅ internal/observability/simulation.go: ticks/stages/actions/lag/heartbeat; runner и worker exporter подключены |
| 17.3 | Game metrics: active players, loaded chunks, buildings placed, resources produced/spent, прямые атаки, monsters | `backend/internal/service/metrics.go` | 🟡 технические и queue метрики есть; полный набор игровых счётчиков экономики/прямого PvP отсутствует |
| 17.4 | Panic/error reporting middleware: recovery marker, stack trace в dev, безопасный error event в prod; optional Sentry | `backend/internal/adapter/http/middleware/common.go`, `backend/internal/adapter/http/router.go` | ✅ production пишет только маркер/request ID, development сохраняет подробности; оба режима проверены тестом |
| 17.5 | Frontend telemetry: runtime errors, WS reconnects, asset load failures, FPS warnings без персональных данных | `frontend/src/shared/telemetry/`, `frontend/src/game/performance/` | 🟡 локальные performance/audio diagnostics есть; общий канал клиентских ошибок/WS/ассетов отсутствует |
| 17.6 | Инфраструктура логов/метрик: Loki/Promtail или Docker logging driver, Prometheus, Grafana dashboards | `deploy/observability/`, `docker-compose.observability.yml` | 🟡 Prometheus/Grafana и Docker logs есть; централизованный сбор логов не настроен |
| 17.7 | Dashboards/runbooks: slow requests, WS degradation, simulation lag, Redis/DB issues, frontend blank canvas | `docs/operations/observability.md`, `deploy/observability/` | 🟡 dashboards/alerts/runbooks и baseline есть; Redis/client и браузерная приёмка не завершены |

---

## Фаза 18 — Деплой и runtime-инфраструктура

| # | Что | Файлы | Статус |
|---|---|---|---|
| 18.1 | Backend Dockerfile: multi-stage build, non-root runtime, CA certificates, healthcheck | `backend/Dockerfile` | ✅ образ собран; UID 10001, CA и healthcheck `/health` проверены в запущенном контейнере |
| 18.2 | Frontend Dockerfile/nginx: React build, SPA fallback, static asset cache headers | `frontend/Dockerfile`, `deploy/Caddyfile` | ✅ production-образ собран; через HTTPS проверены SPA fallback, версия JS-ассета, immutable cache и security header Caddy |
| 18.3 | Production compose: frontend, backend, postgres, redis, worker, volumes, healthchecks, restart policies, private networks | `docker-compose.yml`, `docker-compose.production.yml` | ✅ временный production Compose запущен и очищен; API со встроенным worker, PostgreSQL, Redis, Caddy, volumes, зависимости и healthchecks проверены |
| 18.4 | Prod env-шаблон: обязательные секреты, CORS, JWT TTL, DB/Redis DSN, public URLs, simulation limits | `.env.prod.example`, `backend/.env.prod.example`, `frontend/.env.production.example` | 🟡 секреты, TTL, CORS одного домена, URL ассетов и лимиты проброшены; внешний домен, проверка секретов и все публичные URL ещё не приняты |
| 18.5 | Reverse proxy Caddy: HTTPS termination, HTTP→HTTPS redirect, `/api/*`, `/ws`, SPA fallback, upload/body/timeout limits | `deploy/Caddyfile`, `docs/operations/production.md` | 🟡 локальные HTTPS, redirect, API/WS, SPA, кеш, 1 МБ body limit и Caddy timeout-конфигурация прошли; внешний домен и поведение timeout под нагрузкой не проверены |
| 18.6 | Операционные команды: migrate, seed dev, backup/restore DB, deploy, rollback, logs, shell | `Makefile`, `scripts/`, `docs/operations/deploy.md` | 🟡 миграции, backup и restore в отдельную БД прошли; откат к образам предыдущего релиза и полный operational набор остаются |
| 18.7 | Security hardening: secure headers, cookie/token policy, admin endpoints restricted, metrics/internal protection | `deploy/nginx/`, `backend/internal/adapter/http/middleware/`, `docs/operations/security.md` | 🟡 HTTPS headers, запрет `/metrics`/`/debug` и отказ чужому Origin проверены; политика текущих localStorage-токенов и admin-доступа описана, целевой внешний аудит остаётся |
| 18.8 | Runtime validation checklist: cold start, migration, WS through proxy, static assets, health/readiness, graceful shutdown | `docs/operations/deploy.md`, `tests/e2e/deploy-smoke.md` | 🟡 одноразовая репетиция прошла cold start, миграции, HTTPS/API/WS, /ready, assets, сбои/restore и SIGTERM без принудительного убийства; внешний стенд остаётся |

---

## Фаза 19 — CI/CD

| # | Что | Файлы | Статус |
|---|---|---|---|
| 19.1 | GitHub Actions CI frontend: install, lint, typecheck, unit tests, build | `.github/workflows/frontend-ci.yml` | 🟡 frontend-ci.yml выполняет npm ci/test/build; локально тесты и сборка проходят, lint остаётся |
| 19.2 | GitHub Actions CI backend: gofmt check, go vet, golangci-lint, unit tests, build | `.github/workflows/backend-ci.yml` | 🟡 CI format/vet/race/build, PostgreSQL/Redis и restart smoke добавлен; lint и подтверждённый прогон CI остаются |
| 19.3 | Integration CI: docker compose services, migrations, API smoke, Playwright smoke | `.github/workflows/integration.yml` | 🟡 backend/browser CI и production-rehearsal готовят сервисы/миграции/API/Playwright; успешная серверная/сквозная приёмка не подтверждена |
| 19.4 | Docker pipeline: build frontend/backend images, scan, tag by commit/version, push по main/tag | `.github/workflows/docker.yml` | 🟡 workflow сборки, Trivy и публикации SHA/версии добавлен; запуск в GitHub и опубликованные образы ещё не проверены |
| 19.5 | Contract freshness checks: OpenAPI generated, shared types/catalog schemas current | `.github/workflows/contract.yml`, `scripts/check_contracts.sh` | 🟡 Локальная генерация и freshness-проверка OpenAPI на 79 HTTP-операций пройдены; успешный CI-прогон всей contract workflow ещё нужен |
| 19.6 | CD-процесс: manual approval, deploy/rollback workflow или documented deployment для выбранного стенда | `.github/workflows/deploy.yml`, `docs/operations/deploy.md` | ⏳ |

---

## Фаза 20 — Финальная документация

| # | Что | Файлы | Статус |
|---|---|---|---|
| 20.1 | README проекта: назначение, стек, быстрый старт, команды, архитектура, ссылки на документацию | `README.md` | 🟡 README содержит структуру и команды; описание симуляции устарело, полный текущий quick start/ограничения нужны |
| 20.2 | Product overview: сеттинг, core loop, карта, экономика, PvE/PvP, ограничения MVP | `docs/product/overview.md` | ⏳ |
| 20.3 | User guide: регистрация, карта, строительство, ресурсы, защита, монстры, прямые атаки, чат/союзы, рынок | `docs/product/user-guide.md` | ⏳ |
| 20.4 | Architecture docs: backend, frontend, realtime, simulation, storage, asset pipeline, deployment | `docs/architecture/` | 🟡 overview/api/realtime/worker документы есть; общая сверка с прямым PvP и текущим runtime нужна |
| 20.5 | API reference: OpenAPI, WS protocol, event catalog, error model, pagination/versioning | `docs/api/`, `backend/docs/swagger/` | 🟡 OpenAPI/shared events/API policy есть; полная актуальная API/WS reference не завершена |
| 20.6 | Operations docs: deploy, observability, troubleshooting, backup/restore, security | `docs/operations/` | 🟡 production, backup/restore, observability и текущая политика безопасности описаны; внешний runbook и полная релизная сверка остаются |
| 20.7 | Game design docs: balance tables, building/resource/monster catalog, IP boundaries, future roadmap | `docs/game-design/`, `shared/balance/` | 🟡 building/game-design/balance v2 docs есть; финальная сверка и приёмка контента не выполнены |
| 20.8 | Финальный паспорт playable MVP: реализованные функции, known limitations, проверочный чеклист, demo scenario | `docs/final-mvp.md` | ⏳ |
| 20.9 | Синхронизация design docs с сеттингом Эолии: монеты, эолийские кристаллы, нефть/бензин, жилье, поля/грядки, Союзный дом, цикличный мир | `docs/game-design/visual-style-and-setting-options.md`, `docs/game-design/setting.md`, `docs/product/overview.md` | 🟡 Эолия и прямой конфликт описаны; все исторические design docs ещё требуют синхронизации |

---

## Фаза 21 — Полное покрытие построек спецификациями и балансом

Результат фазы — единый проверяемый реестр всех доступных и запланированных типов построек. Для каждого `building_id` нужны текстовая спецификация в `docs/buildings/`, машиночитаемые характеристики в игровом каталоге и отдельная визуальная спецификация в `docs/assets/specs/`, если объекту требуется модель. Уже существующий файл считается готовым только после сверки уровней, цен, производства, ограничений и состояний с каталогом. Этап развивает пункты 4.1–4.13, 5.1–5.15, 14.7 и 20.7.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 21.1 | Собрать инвентаризацию `building_id` из backend/shared-каталогов, всех `docs/buildings/`, `docs/assets/specs/` и runtime-манифестов; отметить отсутствующие, дублирующиеся и устаревшие id, категорию, число уровней и степень готовности | `docs/buildings/catalog-coverage.md`, `backend/internal/domain/catalog/`, `shared/catalog/`, `docs/assets/specs/` | ✅ |
| 21.2 | Закрепить единый шаблон текстовой спеки: роль, доступность, footprint/место, уровни, цены и время, производство/потребление, хранилище, здоровье, оборона, разрушение/ремонт, визуальные отличия, действия игрока, ограничения, связи с ресурсами и критерии проверки | `docs/buildings/building-characteristics-template.md`, `docs/buildings/tables/templates/` | ✅ |
| 21.3 | Описать все центры и уникальные управляющие постройки, включая ратушу: уровни, зона применения эффектов, строительство, апгрейды, захват/потеря и состояние после разрушения | `docs/buildings/center/`, `shared/catalog/buildings.ts` | ✅ (действующий центр и будущий захват разграничены) |
| 21.4 | Покрыть все жилые ветки и каждый игровой уровень: население, рабочие, вместимость, стоимость, внешний рост от землянки до позднего жилья, доступность после разрушения | `docs/buildings/houses/`, `shared/catalog/buildings.ts` | ✅ (выявлено отсутствие серверной вместимости жилья) |
| 21.5 | Покрыть все поля и грядки: рост по стадиям, время, урожайность, повторный посев, супер-версия, сезонные/ресурсные ограничения и отличия уровней | `docs/buildings/fields/`, `backend/internal/domain/catalog/`, `shared/catalog/buildings.ts` | ✅ (игровой цикл и проектные ограничения разграничены) |
| 21.6 | Покрыть все мастерские, добывающие и перерабатывающие здания: входы/выходы, рабочие, топливо, складские лимиты, остановка, цепочки ресурсов и уровни, включая отсутствующие в каталоге отрасли | `docs/buildings/industry/`, `docs/buildings/resource-buildings/`, `shared/catalog/buildings.ts` | ✅ (34 ID; действующие рецепты отделены от проектных ролей) |
| 21.7 | Разрешить конфликты предметной модели: нефть и растительное масло, эолиевый сплав без resource id, разные названия/стоимости одного объекта и проектные уровни, которых нет в runtime | `docs/game-design/resources-list.md`, `docs/game-design/economy-audit.md`, `docs/buildings/catalog-coverage.md`, `shared/catalog/resources.ts` | ✅ |
| 21.8 | Покрыть склады, хранилища монет, торговые и социальные постройки: ёмкость, доступ, комиссии, казна, права союза, лимиты и последствия повреждения | `docs/buildings/storage/`, `docs/buildings/trade/`, `docs/buildings/social/` | ✅ (активные правила и проектные функции разделены) |
| 21.9 | Покрыть дороги, стены и мостовые: стоимость за сегмент, проходимость, логистика, урон, ремонт, стыки и отображение при соседстве | `docs/buildings/roads/`, `docs/buildings/defense/`, `shared/catalog/buildings.ts` | ✅ (текущие правила и будущая логистика разделены) |
| 21.10 | Покрыть все оборонные постройки, ловушки и базы защитников: дальность, цель, боеприпасы/энергия, перезарядка, взаимодействие с PvE/PvP, контрмеры и баланс массовой обороны | `docs/buildings/defense/`, `docs/game-design/player-defenders.md`, `docs/game-design/defense-expansion-plan.md` | ✅ (спеки; создание защитников и PvP остаются отдельной реализацией) |
| 21.11 | Описать захватываемые руины и объекты на редких клетках: условия захвата, удержание, восстановление, ресурсы, ограничения на размещение и потерю контроля без территориального запрета строительства | `docs/buildings/ruins/`, `docs/buildings/resource-buildings/`, `docs/game-design/` | ✅ захват, длительное восстановление и освобождение клетки после продажи/разрушения реализованы |
| 21.12 | Для каждого типа и уровня сверить документ с backend/shared-каталогом, API и frontend: один id, доступность, цены, характеристики, единицы измерения и русское имя; зафиксировать решение при каждом расхождении | `docs/buildings/catalog-coverage.md`, `backend/internal/domain/catalog/`, `shared/catalog/`, `frontend/src/features/buildings/` | ✅ после обновления реестра башни `make catalog-check` проходит: 72 типа, уровни и API/catalog согласованы; проектные типы и уровни отмечены отдельно |
| 21.13 | Перевести утверждённый баланс в версионируемые данные каталога с проверкой схемы: экономика, строительство, энергия/бензин, PvE/PvP; миграции и совместимость сохранённого мира при изменении баланса | `data/buildings/`, `data/balance/v2.json`, `backend/internal/domain/catalog/`, `backend/db/migrations/`, `docs/game-design/balance-versioning.md` | ✅ v2 и схема проверяются; миграция 000038 прогнана на PostgreSQL 16: уровень/доля HP, разрушенные здания и сохранность строк проверены |
| 21.14 | Добавить автоматическую проверку покрытия: каждый доступный `building_id` имеет текстовую и визуальную спеку либо явное исключение, все уровни и ресурсы существуют, стоимость неотрицательна, ссылки на ассеты разрешаются | `docs/buildings/check-coverage.py`, `docs/buildings/catalog-coverage.md`, `docs/assets/specs/schema.json` | ✅ после обновления реестра башни `make catalog-check` проходит: 72 типа, 80 ресурсов, уровни, спеки и ссылки; полнота production-моделей отдельно учитывается фазой 22 |
| 21.15 | Проверить игровые цепочки вручную и тестами: первое поселение, жильё/рабочие, добыча, производство, хранение, оборона, апгрейд, разрушение и восстановление без тупиков в ресурсах | `docs/game-design/economy-audit.md`, `backend/internal/domain/catalog/*_test.go`, `frontend/tests/e2e/` | 🟡 Go catalog/service тесты проходят, но аудит выявляет ресурсы без источника/рецепта и цены апгрейдов, зависящие от них; полный сценарий без тупиков не пройден. Пробелы и пакет исправлений — в [аудите экономики](../game-design/economy-audit.md) |
| 21.16 | Сверить пять уровней многоквартирного дома с игровой реализацией, балансом и моделями, затем принять характеристики и переходы | `docs/buildings/houses/apartment-house.md`, `data/buildings/`, `frontend/public/assets/buildings/` | 🟡 спецификация уровней подготовлена; соответствие игры и моделей требует отдельной проверки |

---

## Фаза 22 — Полный набор игровых моделей, анимаций и визуальная интеграция

Текущий пайплайн Blender и часть семейств PNG/GLB уже существуют; статус отдельных семейств зафиксирован в [журнале ассетов](../assets/asset-generation-status.md). Эта фаза считается завершённой по итоговому покрытию каталога и проверке в игре, а не по наличию одной тестовой модели. Она конкретизирует фазу 14 и [план фабрики моделей](../assets/blender-asset-factory-plan.md).

Порядок работы и конкретные пробелы 22.3–22.7 зафиксированы в [очереди производства](../assets/phase-22-3-7-execution.md). 03.11.2026 Blender MCP проверен повторно и недоступен; без живой сцены нельзя выполнить обязательные screenshot-review и приёмку новых production-моделей. Сканер 22.1 обновлён по каталогу: 72 типа, 42 неполных семейства или отсутствующих production manifest. Наличие visual-spec и файлов ассетов само по себе не означает приёмку модели.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 22.1 | Сопоставить каждый тип и уровень из реестра 21.1 с asset id, `.blend`, PNG, GLB LOD0–2, `manifest`, `report`, статусом подключения и обязательными состояниями; отделить тестовые варианты от production | `docs/assets/building-asset-coverage.md`, `docs/assets/scan-building-assets.py`, `frontend/public/assets/buildings/` | 🟡 инвентаризация пересоздана `python3 docs/assets/scan-building-assets.py`: 72 типа, 42 неполных семейства/отсутствующих manifest; сверка покрытия обновлена, production-ассеты не принимались визуально |
| 22.2 | Утвердить общий контракт визуальной спеки: footprint, размер/камера, origin/anchor, цвет и материалы, стадии строительства, `active/damaged/ruined`, LOD, экспорт и допустимые бюджеты | `docs/assets/building-asset-contract.md`, `docs/assets/specs/schema.json`, `docs/assets/specs/template.yaml` | ✅ |
| 22.3 | Довести семейства центров и жилья до полного набора уровней и состояний; исключить подмену стройки или повреждения готовой моделью там, где по плану требуется отдельная геометрия | `docs/assets/specs/center/`, `docs/assets/specs/housing/`, `frontend/public/assets/buildings/center/`, `frontend/public/assets/buildings/housing/` | 🟡 центры/раннее и часть позднего жилья созданы; ратуша 1–15 имеет 45 вариантов, LOD0 до 28002 треугольников требует оптимизации/приёмки |
| 22.4 | Сгенерировать и проверить все недостающие семейства полей и грядок: стадии роста, урожай, супер-версия, стройка, повреждение, руина и различимые уровни | `docs/assets/specs/fields/`, `tools/assets/blender/real_city/components/`, `frontend/public/assets/buildings/fields/` | 🟡 несколько полей имеют уровни/рост/состояния; отсутствующие семейства/LOD/супер-стадии ещё нужно закрыть |
| 22.5 | Сгенерировать все недостающие промышленные и ресурсные постройки: читаемые входы/выходы производства, топливо, механизмы, уровни, остановка, повреждение и руины | `docs/assets/specs/industry/`, `tools/assets/blender/real_city/components/`, `frontend/public/assets/buildings/industry/` | 🟡 многие промышленные семейства уже сгенерированы; оставшиеся типы/LOD/руины и соответствие v2 не закрыты |
| 22.6 | Создать семейства склада, рынка, союзного дома, обороны, ловушек, дорог и стен по их текстовым спекам; проверить соседство сегментов, зоны атаки и визуальную читаемость владельца | `docs/assets/specs/`, `frontend/public/assets/buildings/`, `tools/assets/blender/real_city/components/` | 🟡 грунтовая, обычная и мощёная дороги пересобраны во всех 16 формах и четырёх состояниях и подключены; стыки прошли проверку геометрии/PNG, но визуальная проверка смешанной сети в игре, а также полный набор социальных/торговых/защитных объектов не приняты |
| 22.7 | Завершить природный набор: тайлы, лес и вырубка/восстановление, горы, реки, месторождения, редкие клетки и руины; проверить переходы границ и совместимость с цикличной картой | `docs/assets/terrain-regeneration-brief.md`, `frontend/public/assets/terrain/`, `frontend/public/assets/resources/` | 🟡 terrain/resources/ruins и генераторы есть; единая визуальная приёмка переходов/швов отсутствует |
| 22.8 | Создать оригинальные модели/спрайты всех видов монстров и защитников с необходимыми состояниями движения, атаки, урона и гибели | `docs/game-design/monster-specs.md`, `docs/assets/monster-sprites-and-animation-plan.md`, `frontend/public/assets/monsters/` | 🟡 monster registry/assets и спецификации есть; все состояния/защитники не приняты |
| 22.9 | Реализовать экспорт и проигрывание только нужных игровых анимаций: движение, производство, удары, предупреждения, рост; задать паузу/редукцию движения и предел одновременных эффектов | `docs/assets/animation-export-conventions.md`, `tools/assets/`, `frontend/src/game/renderers/` | 🟡 animation registry/clock, loader и fixtures реализованы; полный production экспорт всех требуемых анимаций не завершён |
| 22.10 | Автоматически проверять все артефакты: размеры и alpha PNG, имена состояний, bounds/footprint, три LOD, число полигонов, материалы, manifest, URL и отсутствие пустых файлов | `tools/assets/`, `frontend/scripts/check-asset-budget.mjs`, `docs/assets/specs/` | 🟡 отдельные валидаторы PNG/GLB/LOD/ground/manifest есть; весь каталог единой проверкой не принят |
| 22.11 | Подключить каждое утверждённое семейство к runtime lookup и проверить рендер на карте, в инспекторе и 3D-просмотре; для 3D-сцен использовать Three.js | `frontend/src/game/`, `frontend/src/game/assets/`, `frontend/public/assets/buildings/` | 🟡 runtime lookup, Pixi и Three previews подключены для части семейств; приёмка каждого типа/уровня не завершена |
| 22.12 | Проверить контактные листы и игровые скриншоты каждого семейства на масштабе карты: силуэт, различимость уровней/состояний, тени, стыки земли и читаемость на мобильном экране | `docs/assets/asset-generation-status.md`, `docs/assets/review/`, `frontend/tests/visual/` | 🟡 contact sheets и история review отдельных партий есть; все семейства на карте/mobile не проверены |
| 22.13 | Ввести бюджеты первоначальной загрузки, чанка, памяти текстур и GLB; загрузку по видимости, fallback и очистку ресурсов при уходе чанка | `frontend/src/game/assets/`, `frontend/src/game/performance/`, `frontend/scripts/check-asset-budget.mjs` | 🟡 assets:budget проходит (885.4 MB/5829 runtime файлов); бюджеты памяти, visibility unload и стартовой загрузки не приняты |
| 22.14 | Сверить визуальный список с реестром 21.1: ни одна доступная постройка, уровень или обязательное состояние не остаются без утверждённого ассета либо явно указанного временного fallback | `docs/buildings/catalog-coverage.md`, `docs/assets/asset-generation-status.md`, `scripts/check-building-coverage.*` | 🟡 реестры и fallback существуют; актуальная сверка v2 и всех обязательных состояний ещё нужна |
| 22.15 | Переработать иконки ресурсов по материалам и текстурам, подключить их поэтапно и проверить читаемость и соответствие каталогу | `docs/assets/resource-icon-rework-plan.md`, `frontend/public/assets/`, `frontend/src/` | 🟡 план переработки подготовлен; создание, замена и визуальная приёмка остаются |

---

## Фаза 23 — Генерация аудио и игровой звук

Детальная матрица звуков, рецепты, частичный набор WAV/MP3 и задачи подключения описаны в [плане аудио](audio-effects-plan.md). Здесь зафиксирован результат для полной игры: оригинальный воспроизводимый каталог эффектов, подключённый к подтверждённым действиям. Фоновая музыка и озвучка остаются отдельным решением о масштабе выпуска.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 23.1 | Сверить матрицу событий с актуальными API/WS-командами и экранными действиями: различать локальный UI-отклик, серверное подтверждение, удалённое событие и пассивный тик | `docs/audio/event-matrix.md`, `shared/events/`, `frontend/src/features/` | 🟡 event matrix/soundEvents/realtimeAudio есть; после удаления рейдов нужна окончательная сверка прямого PvP |
| 23.2 | Довести реестр `sound_id` и происхождения до полного покрытия: собственный рецепт или запись, автор/лицензия, версия, варианты, игровое событие, приоритет и шина | `docs/audio/asset-register.md`, `docs/audio/sound-style.md`, `tools/audio/recipes/` | 🟡 recorded-sources и лицензии CC0 описаны; исторические количества/рейдовые строки и соответствие текущему manifest требуют сверки |
| 23.3 | Провести слепое прослушивание уже созданных пилотных звуков и выбрать финальные варианты на наушниках, ноутбуке и телефоне; записать решения по тембру и громкости | `docs/audio/listening-review.md`, `tools/audio/review/` | ⏳ |
| 23.4 | Сгенерировать/записать и собрать все эффекты интерфейса, выбора, подтверждений, ошибок, предупреждений и доступности с вариациями для частых действий | `tools/audio/recipes/ui.json`, `tools/audio/master/`, `frontend/public/assets/audio/ui/` | 🟡 UI MP3/master/manifest существуют и используются; художественная/громкостная приёмка не выполнена |
| 23.5 | Сгенерировать экономические эффекты: монеты, кристаллы, добыча каждого материала, сбор полей, производство, остановка по топливу, торговля и награда; пакетные события озвучивать один раз | `tools/audio/recipes/`, `frontend/public/assets/audio/economy/`, `docs/audio/event-matrix.md` | 🟡 экономические записи и wiring есть; полнота подтверждённых событий зависит от завершения рынка/экономики |
| 23.6 | Сгенерировать строительство и мир: установка, стадии, завершение, апгрейд, ремонт, дорога, стена, разрушение, лес, руины и редкие ресурсы | `tools/audio/recipes/`, `frontend/public/assets/audio/build/`, `frontend/public/assets/audio/world/` | 🟡 build/world эффекты и wiring существуют; финальная сценарная/громкостная приёмка нужна |
| 23.7 | Завершить семейства PvE/PvP: индивидуальные выстрелы орудий, попадание, защита, монстры во всём видимом viewport, тревога и исход боя; проверить слышимость и баланс | `tools/audio/recipes/`, `frontend/public/assets/audio/combat/`, `frontend/public/assets/audio/monsters/` | 🟡 звуки орудий и монстров в видимой области подключены; акустическая и игровая приёмка, включая прямой PvP, остаётся |
| 23.8 | Создать ненавязчивые петли окружения и социальные сигналы для чата/союза/рынка; предусмотреть выключение атмосферы и подавление спама сообщений | `tools/audio/recipes/`, `frontend/public/assets/audio/ambience/`, `frontend/public/assets/audio/social/` | 🟡 ambience/music/socialAudio и настройки реализованы; приёмка петель/спама и связи с WS не завершена |
| 23.9 | Реализовать воспроизводимую сборку WAV master → обработка → MP3/резервный формат → manifest; проверки клиппинга, тишины, хвостов, длительности, формата и размера | `tools/audio/build_audio.py`, `tools/audio/validate_audio.py`, `frontend/public/assets/audio/manifest.json` | 🟡 build/import/version/validate_audio и audio CI есть; воспроизводимость из внешнего source cache и резервный формат не приняты |
| 23.10 | Подключить Web Audio: запуск после жеста, шины UI/world/alerts/ambience, общая громкость и mute, лимит голосов, приоритеты, кеш, вариации и сохранение настроек | `frontend/src/audio/`, `frontend/src/features/settings/`, `frontend/src/shared/store/` | 🟡 AudioManager/graph/voices/settings/Provider реализованы и тестируются; мобильная приёмка/ограничения браузеров остаются |
| 23.11 | Связать звук с подтверждёнными ответами и `event_id`, убрать дубли HTTP/WS и повторы после reconnect; добавить затухание по расстоянию и видимости для мировых событий | `frontend/src/audio/`, `frontend/src/shared/realtime/`, `frontend/src/features/world/` | 🟡 event_id dedupe, spatialAudio и тесты есть; все действия/reconnect/прямой PvP ещё нужно проверить |
| 23.12 | Проверить сценарии без звука, autoplay block, мобильные браузеры, фоновые вкладки и слабую сеть; измерить бюджет первой загрузки и итоговый баланс громкостей | `frontend/tests/e2e/audio.spec.ts`, `docs/audio/listening-review.md`, `frontend/scripts/check-asset-budget.mjs` | 🟡 unit tests и budget проходят; audio Playwright/mobile/listening review не выполнены |

---

## Фаза 24 — Редизайн игровой поверхности

Работа ведётся по [плану редизайна](interface-redesign-plan.md). Первый экран остаётся картой и действиями игрока. Редизайн принимает реальные сценарии и ассеты игры; он должен улучшить читаемость управления, не подменяя игровую механику. Этап конкретизирует фазу 3 и визуальную часть фаз 14/16.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 24.1 | Зафиксировать текущие desktop/mobile скриншоты, маршруты игрока и проблемы иерархии, плотности, перекрытия карты, адаптивности и доступности | `docs/plans/interface-redesign-audit.md`, `docs/assets/ui/review/`, `frontend/src/features/` | ⏳ |
| 24.2 | Утвердить арт-направление Эолии и интерактивный макет главного экрана на реальном фрагменте карты: HUD, выбор, стройка, события, тревога, чат и инспектор | `docs/art/aeolian-ui-style-guide.md`, `docs/assets/ui/review/` | 🟡 visual-style-guide.md есть; интерактивный макет/утверждённая полная система не зафиксированы |
| 24.3 | Реализовать токены цветов, типографики, отступов, размеров, слоёв, теней и состояний без разнобоя между CSS и Pixi overlays | `frontend/src/app/styles/`, `frontend/src/shared/ui/`, `frontend/src/game/overlays/` | 🟡 текущие styles/tokens/UI есть; согласованная новая тема CSS/Pixi не завершена |
| 24.4 | Переработать HUD ресурсов, статусы угроз и связи, панель инструментов и уведомления: важное видно сразу, длинные числа не ломают сетку, карта остаётся главным полем | `frontend/src/features/hud/`, `frontend/src/features/tools/`, `frontend/src/features/notifications/` | 🟡 существующий HUD/tools/notifications работают; редизайн и проверка длинных чисел/перекрытий остаются |
| 24.5 | Переработать каталог строительства: категории, поиск/фильтры, карточка уровня, цена/время/условия, выбор места, предпросмотр footprint и понятная причина запрета | `frontend/src/features/buildings/`, `frontend/src/features/build-placement/`, `frontend/src/game/overlays/` | 🟡 BuildMenu и placement уже есть; завершение редизайна/поиска/причин запрета нужно принять отдельно |
| 24.6 | Переработать инспектор клетки, своей/чужой постройки, ресурса, монстра, руины и игрока: собственник, состояние, доход, защита, риск и доступные действия с серверными причинами запрета | `frontend/src/features/inspector/`, `frontend/src/features/player/`, `frontend/src/features/inspector/` | 🟡 Inspector содержит свои/чужие объекты и действия; новая компоновка/полнота серверных причин не приняты |
| 24.7 | Переработать журнал событий, чат, союз, рынок, профиль и настройки: очередность уведомлений, контекстные переходы на карту, непрерывность действий при realtime-обновлении | `frontend/src/features/event-log/`, `frontend/src/features/chat/`, `frontend/src/features/alliance/`, `frontend/src/features/market/`, `frontend/src/features/player/` | 🟡 текущие социальные/профильные панели есть; непрочитанное и непрерывность realtime не завершены |
| 24.8 | Создать оригинальный набор UI-иконок и умеренный декор; сверить палитру с террейном, зданиями и эффектами, предусмотреть fallback при загрузке | `frontend/public/assets/ui/`, `docs/art/aeolian-ui-style-guide.md`, `frontend/src/shared/ui/` | ⏳ |
| 24.9 | Реализовать отдельные компактные компоновки для планшета/телефона, touch-цели, жесты карты и альтернативы hover без перекрытия ключевого действия | `frontend/src/app/styles/`, `frontend/src/game/camera/`, `frontend/src/features/` | 🟡 текущий mobile fallback есть; отдельная приёмка touch/hover/safe-area отсутствует |
| 24.10 | Добавить клавиатурный маршрут и доступные состояния: focus, Escape/возврат фокуса, контраст, reduced motion, сообщения об ошибках и статусе без потока объявлений от тиков | `frontend/src/shared/ui/`, `frontend/src/app/styles/`, `docs/frontend/controls.md` | 🟡 Modal поддерживает начальный фокус, Tab/Shift+Tab, Escape, возврат фокуса и стек окон; keyboard test проходит; общий маршрут, контраст/reduced-motion/скринридер остаются |
| 24.11 | Связать визуальный и звуковой отклик: локальный выбор, ожидание сервера, успех/ошибка и тревога; состояние действия показывать и без звука | `frontend/src/features/`, `frontend/src/audio/`, `docs/audio/event-matrix.md` | 🟡 playUiSound и серверные подтверждения уже подключены; единая визуальная обратная связь и сценарий mute не приняты |
| 24.12 | Провести визуальные и сценарные проверки desktop/mobile, клавиатуры и скринридера; сравнить до/после FPS, время реакции и долю доступной карты | `frontend/tests/e2e/ui.spec.ts`, `frontend/tests/visual/`, `docs/assets/ui/performance-review.md` | 🟡 mock UI/Pixi spec и Playwright runner есть; живая приёмка, сравнение до/после и проверка скринридером не выполнены |
| 24.13 | Включить новую тему поэтапно, проверить игровые API/WS действия и откат без миграций данных; обновить финальный style guide и инструкции компонентов | `frontend/src/app/`, `docs/operations/ui-rollout.md`, `docs/art/aeolian-ui-style-guide.md` | ⏳ |
| 24.14 | Рассмотреть внедрение подобранных шрифтов после решения об изменении действующего дизайн-плана; при положительном решении проверить конкретные файлы, лицензию, кириллицу и интерфейсные состояния | `docs/art/font-options.md`, `frontend/src/app/styles/` | 🟡 варианты подобраны; дизайн-план пока сохраняет действующий стек, решение о внедрении и проверка в игре остаются |

---

## Фаза 25 — Замыкание игровых механик и цельный игровой цикл

Фаза собирает ещё не завершённые пункты 1–13 в единую последовательность действий и устраняет зависимость от демонстрационных заглушек. Для актуального направления фаза 9 с контролируемой территорией остаётся исключённой; правила строительства на свободной клетке, владения объектом и спорных ресурсов проверяются отдельно.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 25.1 | Завершить расширенный профиль, уровни/XP и достижения на основе подтверждённых игровых событий; разделить публичные и приватные данные | `backend/internal/service/profile.go`, `backend/internal/service/experience.go`, `frontend/src/features/player/` | 🟡 единый каталог уровней и базовые profile/XP есть; расширение профиля и значки не завершены; агрегированные числовые оценки исключены пунктом очереди 1 |
| 25.2 | Завершить цикличную карту: wrap координат и чанков, pathfinding через шов, отсутствие дублей объектов и корректные камера/selection | `backend/internal/domain/world/`, `backend/internal/service/world.go`, `frontend/src/game/` | 🟡 wrap реализован частями; сквозная приёмка швов/selection/pathfinding нужна |
| 25.3 | Довести размещение и апгрейды всех утверждённых построек до серверных правил стоимости, занятости клетки, уровня, лимитов, прав, таймеров и атомарной записи ресурсов | `backend/internal/service/building.go`, `backend/internal/domain/building/`, `frontend/src/features/buildings/` | 🟡 place/upgrade/complete/cancel/demolish/relocate получили транзакционные границы и блокировки; добавлены матрицы типов/уровней, SQL/race-прогон остаётся |
| 25.4 | Замкнуть экономику: добыча и конкуренция за узлы, поля, производство, рабочие, топливо, склад, торговля, офлайн-прогресс и понятные UI-причины остановки | `backend/internal/service/economy.go`, `backend/internal/worker/simulation/`, `frontend/src/features/economy/` | 🟡 шахта/канатный двор и редкие выходы реализованы; производство/поля транзакционны, авто-сделки рынка есть; достижимость всех цепочек и живой прогон не приняты |
| 25.5 | Завершить PvE и оборону: монстры, защитники, орудия, ловушки, расход ресурсов, выбор целей и восстановление после потерь | `backend/internal/service/combat.go`, `backend/internal/service/defense.go`, `frontend/src/features/threat/` | 🟡 исправлен огонь орудий по собственным монстрам, добавлены матрица уровней и rollback выстрела; полная приёмка защитников/ловушек/восстановления остаётся |
| 25.6 | Завершить прямой PvP оружием/бомбами и созданными монстрами: стоимость, дальность, задержки, урон, cooldown, защита от злоупотреблений, ремонт и уведомления обеим сторонам; рейды исключены | `backend/internal/service/pvp.go`, `backend/internal/service/combat.go`, `backend/internal/service/building.go`, `frontend/src/features/inspector/` | 🟡 оружие/бомбы/монстры и ремонт реализованы; офлайн-защита и дневной бюджет потерь сохраняются в PostgreSQL; серверная и игровая приёмка остаются |
| 25.7 | Завершить социальный контур: постоянные репозитории союза/казны/рынка, leave/kick, роли, unread, realtime, сделки и модерацию чата | `backend/internal/adapter/postgres/`, `backend/internal/service/alliance.go`, `backend/internal/service/market.go`, `frontend/src/features/` | 🟡 persistence/leave/kick/leadership/WS/unread и авто-сделки реализованы, frontend проверен; SQL/live приёмка и полный контур модерации остаются |
| 25.8 | Довести API и realtime-контракт до одной версии: идемпотентность опасных POST, OpenAPI/WS-события, коды ошибок, typed client и миграции совместимости | `backend/docs/swagger/`, `shared/`, `frontend/src/shared/api/`, `backend/internal/adapter/ws/` | 🟡 OpenAPI описывает 79 HTTP-операций, typed client и события обновлены; freshness/Go/SQL/live проверка и совместимость миграций остаются |
| 25.9 | Завершить администрирование: права, аудит, диагностические экраны, безопасную модерацию и проверку запрета доступа обычного игрока | `backend/internal/service/admin.go`, `backend/internal/adapter/http/handler/admin.go`, `frontend/src/features/admin/` | 🟡 управление аккаунтами/ролями, причина, аудит и отзыв HTTP/WS реализованы; frontend проверен, Go/SQL и полный диагностический контур остаются |
| 25.10 | Провести цельный сценарий на общем сервере: зарегистрироваться → основать поселение → добыть → построить/улучшить → защититься → столкнуться с монстром и соседом → восстановиться → вступить в союз/сделку | `tests/e2e/api/gameplay_restart.py`, `scripts/test-gameplay-restart.sh`, `docs/qa/social-and-repair.md` | 🟡 двухигроковый API/WS-сценарий с картой, боем, союзом, рынком, ремонтом и рестартом прошёл на production Compose; полный браузерный маршрут и часть механик этой строки остаются |
| 25.11 | Проверить конкурентные команды, повтор WS/HTTP, рестарт worker, догоняющие тики и недоверенный клиент: отсутствие двойных наград, отрицательных ресурсов и незаконных действий | `backend/internal/service/**/*_test.go`, `backend/internal/worker/**/*_test.go`, `tests/e2e/api/` | 🟡 добавлены транзакции и concurrency/rollback-матрицы производства, сбора/уничтожения, жизненного цикла и PvP-квот; SQL/race/restart ещё не выполнены |

---

## Фаза 26 — Приёмка, эксплуатация и выпуск

Этот этап конкретизирует общие фазы 15–20. Выпуск определяется работающей общей картой и воспроизводимым запуском; наличие файлов и зелёная сборка сами по себе не закрывают приёмку.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 26.1 | Зафиксировать целевые пороги производительности и измерить карту, 3D-просмотр, крупные чанки, загрузку ассетов, WS fanout, задержку тика и память на desktop/mobile | `docs/performance/performance-audit.md`, `frontend/tests/performance/`, `tests/k6/` | 🟡 свежие короткие HTTP/WS-замеры 10/50 клиентов есть; тик, CPU/RAM, 3D, длительный desktop/mobile профиль остаются |
| 26.2 | Устранить подтверждённые узкие места: incremental rendering, culling, viewport delta, горячие SQL-запросы, кэш с корректной инвалидацией и ограничение очередей | `frontend/src/game/`, `backend/internal/service/world.go`, `backend/internal/adapter/ws/`, `backend/db/query/` | 🟡 DOM bottleneck исправлен, canvas/visibility helpers есть; итоговые измерения остальных узких мест нужны |
| 26.3 | Провести регрессию доменной логики, контрактов, миграций, браузерных сценариев, звука, визуальных состояний и доступности; включить необходимые проверки в CI | `backend/**/*_test.go`, `frontend/tests/`, `.github/workflows/` | 🟡 Go/race, миграции, контракты и API/WS restart прошли; браузерная, звуковая, визуальная и release-приёмка остаются |
| 26.4 | Закрыть контур наблюдаемости: метрики, логи и алерты для API, WS, DB, worker, игрового цикла и загрузки клиентских ассетов; обновить runbooks | `docs/plans/observability-plan.md`, `docs/operations/observability.md`, `deploy/observability/` | 🟡 API/WS/DB/worker dashboards/alerts есть; игровые/client/Redis метрики и приёмка остаются |
| 26.5 | Подготовить production-сборки, секреты, миграции, reverse proxy/WS, healthchecks, резервирование, восстановление и проверенный откат | `deploy/`, `docker-compose.production.yml`, `docs/operations/deploy.md`, `scripts/` | 🟡 образы/Compose/TLS/proxy/backup/restore/shutdown проверены в изолированной репетиции; откат прошлого релиза и внешний стенд не проверены |
| 26.6 | Выполнить smoke на целевом стенде с несколькими игроками и перезапуском сервисов; проверить сохранность общей карты, корректность таймеров и восстановление соединения | `tests/e2e/deploy-smoke.md`, `docs/qa/release-checklist.md` | 🟡 локальный production Compose прошёл двухигроковый API/WS-сценарий и рестарт; целевой внешний стенд, таймеры и браузерный маршрут не проверены |
| 26.7 | Сверить документацию с фактической игрой: быстрый старт, управление, каталог построек, баланс, звук, ассеты, API/WS, ограничения и политика оригинального контента | `README.md`, `docs/product/`, `docs/buildings/`, `docs/audio/`, `docs/architecture/` | 🟡 большой корпус документации есть; общий plan обновлён, остальные документы требуют релизной сверки |
| 26.8 | Составить паспорт версии: выполненные сценарии, измерения, известные ограничения, сценарий демонстрации и дальнейший backlog без скрытых заглушек | `docs/final-mvp.md`, `docs/qa/release-checklist.md`, `docs/plans/plan.md` | ⏳ |

## Фаза 27 — Рабочий процесс Git и интеграция изменений

| # | Что | Файлы | Статус |
|---|---|---|---|
| 27.1 | Инвентаризировать локальную историю и рабочее дерево относительно `origin/main`; сохранить незакоммиченные изменения и определить безопасную стратегию интеграции существующих коммитов без потери истории | `docs/development/git-workflow.md`, Git refs и рабочее дерево | ⏳ локальный `main` опережает `origin/main` на 64 коммита; рабочее дерево содержит незакоммиченные изменения, публикация и группировка пока не разобраны |
| 27.2 | Разложить накопленные изменения по логически связанным задачам и подготовить обозримые PR с описанием и результатами проверок | Git-история, PR в GitHub | ⏳ |
| 27.3 | Привести локальный `main` к согласованной базовой версии и перейти к короткоживущим веткам `feat/`, `fix/`, `chore/` и `docs/` для новых задач | Git branches, `docs/development/git-workflow.md` | ⏳ |
| 27.4 | Установить единый формат коммитов, описания PR и политику слияния для репозитория | `docs/development/git-workflow.md`, настройки GitHub | ⏳ |
| 27.5 | Настроить защиту `main`: запрет прямой записи и force-push, обязательные актуальные CI-проверки и ревью согласно размеру команды | Настройки ветки `main` и GitHub Actions | ⏳ |
| 27.6 | Проверить новый цикл на одной задаче: ветка от актуального `main`, коммиты только по задаче, PR, обязательный CI, слияние и удаление ветки | PR в GitHub, CI, `docs/development/git-workflow.md` | ⏳ |

## Порядок зависимостей

```
Фаза 0 (каркас)
    ├── Фаза 1 (аккаунты, игроки и сессии)
    │       ├── Фаза 2 (мировая карта, координаты и чанки)
    │       │       ├── Фаза 3 (игровой HUD и базовый UI) — параллельно с базовым рендером карты
    │       │       ├── Фаза 4 (здания, размещение и строительство)
    │       │       │       ├── Фаза 5 (экономика, ресурсы и инвентарь)
    │       │       │       │       └── Фаза 7 (симуляция мира, таймеры и фоновые задачи)
    │       │       │       ├── Фаза 9 (территория, владение и защита) — исключена
    │       │       │       ├── Фаза 10 (прямые PvP-атаки, разрушения и ремонт)
    │       │       │       └── Фаза 15 (кэширование, производительность и масштабирование)
    │       │       └── Фаза 8 (монстры, PvE и угрозы) — после базовой карты, чанков и simulation worker
    │       └── Фаза 11 (союзы, чат, рынок и социальные механики)
    ├── Фаза 6 (Realtime WebSocket и события мира) — после auth и базовой карты; затем используется фазами 4–11
    ├── Фаза 12 (middleware, роутер, Swagger и API-контракт) — параллельно с 1–11, но финализируется после стабилизации API
    ├── Фаза 14 (ассеты, визуальный пайплайн и контент) — параллельно frontend/gameplay фазам
    └── Фаза 21 (полное покрытие построек спецификациями)
            └── Фаза 22 (модели, анимации и интеграция)

Фаза 23 (генерация аудио) — после матрицы событий, интеграция после готовности соответствующих механик.
Фаза 24 (редизайн) — после аудита игровых сценариев, параллельно 22–23.
Фаза 25 (цельный игровой цикл) — объединяет результаты механик 1–13 и контента 21–24.
Фаза 26 (приёмка и выпуск) — после 25 и необходимых частей 15–20.

Расширенный профиль игрока из фазы 1 наращивается по мере готовности фаз 4, 5, 8, 10 и 11: эти механики поставляют XP-события, достижения, репутацию и групповой контекст.
Фаза 13 (администрирование и модерация) — после auth, world, realtime и базовых gameplay-сущностей; diagnostics зависят от 7, 15 и 17.
Фаза 16 (тестирование и качество) — наращивается по всем фазам, финальный проход после завершения прикладных фаз 1–15 и 21–25.
Фаза 17 (observability) — после базового logger из 0 и realtime/simulation из 6–7; инфраструктура нужна до production-like деплоя.
Фаза 18 (деплой и runtime-инфраструктура) — после стабилизации сборки frontend/backend, миграций, WS proxy и observability.
Фаза 19 (CI/CD) — после фиксации команд тестирования, сборки, contract generation и docker pipeline.
Фаза 20 (финальная документация) — ведётся по мере реализации; окончательно закрывается после приёмки 26.
Фаза 21 (спеки построек и баланс) — начинается с инвентаризации существующего каталога; решения 21.7–21.13 предшествуют массовой генерации моделей и окончательной настройке экономики.
Фаза 22 (модели и анимации) — использует утверждённые спеки 21; подключение и визуальная проверка идут партиями параллельно игровым механикам и редизайну.
Фаза 23 (аудио) — генерация эффектов идёт после матрицы событий, подключение — после устойчивого API/WS-контракта 25.8; громкостная приёмка следует за редизайном 24.
Фаза 24 (редизайн) — опирается на существующую карту и игровые сценарии; финальные панели проверяются с каталогом 21, ассетами 22 и аудио 23.
Фаза 25 (цельный игровой цикл) — собирает незавершённые части фаз 1–13; сценарий 25.10 возможен после готовности ключевых построек и ресурсов.
Фаза 26 (приёмка и выпуск) — после игровых сценариев 25, интеграции контента 21–24 и необходимых частей фаз 15–20.
Ближайший playable MVP: фазы 0–8, 12 и минимальные части 14–17, 21–25; контролируемая территория из фазы 9 исключена, PvP и production hardening развиваются после подтверждения авторитетного серверного цикла.
```
