# Эксплуатация production

Обновление настроек выпуска и ограничения origin зафиксированы в [очереди 111–120](../plans/queue-111-120.md). Для production Compose задаёт `JWT_ACCESS_TTL=15m`, `JWT_REFRESH_TTL=720h` и `CORS_ALLOWED_ORIGINS=https://DOMAIN`; запрос с чужим `Origin` получает 403 до игрового действия. Caddy ограничивает подключение к API пятью секундами, ожидание заголовков — двадцатью. Подробности хранения токенов и доступа к admin API — в [политике безопасности](security.md).

Workflow `release-images` собирает backend и frontend из текущего commit, сканирует образы Trivy на исправимые HIGH/CRITICAL уязвимости и публикует в GHCR с тегом `sha-<полный SHA>`. Для версии `vX.Y.Z` он также публикует версионный тег того же образа. Запуск workflow не равен проверке внешнего стенда: для выкладки нужны успешная репетиция, резервная копия, проверка восстановления и smoke на целевом домене.

Пример команд оператора после выбора проверенных образов (выполнять в каталоге выпуска с заполненным `.env`):

```bash
docker compose -f docker-compose.production.yml config --quiet
bash scripts/backup-production.sh /srv/backups/real-city-before-release.dump
bash scripts/verify-production-backup.sh /srv/backups/real-city-before-release.dump
docker compose -f docker-compose.production.yml stop backend
docker compose -f docker-compose.production.yml pull backend web
docker compose -f docker-compose.production.yml run --rm backend /app/migrate up
docker compose -f docker-compose.production.yml up -d --wait
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs --since=10m backend web
```

Для отката совместимого кода верните в `.env` прежние `BACKEND_IMAGE` и `FRONTEND_IMAGE`, затем выполните `docker compose -f docker-compose.production.yml up -d --wait backend web`. Схему БД автоматически вниз не мигрируйте. Перед остановкой API убедитесь, что backup действительно создан и восстановлен в отдельной БД; команда выше — процедура, а не запись о выполненном внешнем выпуске.

Для изолированной репетиции добавлен `bash scripts/test-production-local.sh` и workflow `production-rehearsal.yml`. Скрипт использует собственный Compose-проект/volumes, проверяет образы, HTTPS localhost с локальной CA, HTTP→HTTPS, заголовки, закрытие `/metrics` и `/debug`, лимит тела API 1 МБ, API/WS, миграции, сбои хранилищ, backup/restore, рестарт и штатный SIGTERM API. Нужны свободные порты 80/443 и доступ к Docker. `REAL_CITY_ACCEPTANCE_ARTIFACTS` задаёт каталог логов, коротких HTTP/WS-отчётов, `stages.jsonl` и `result.json`. Фактический успешный локальный smoke и ограничения — в [отчёте 101–110](../plans/queue-101-110-implementation.md).

Полная репетиция требует `REAL_CITY_PREVIOUS_BACKEND_IMAGE` и `REAL_CITY_PREVIOUS_FRONTEND_IMAGE` — образы конкретного предыдущего релиза. После проверки backup скрипт переключается на них поверх обновлённой схемы, проверяет HTTPS, клиент, сессию, инвентарь и WS, затем возвращается на новые образы. Оба перехода сохраняют БД; миграции вниз не выполняются. Одинаковые image ID у обеих пар отклоняются. `rollback.json` содержит image ID, длительность и результат только успешно законченного сценария. Нужны образы, доступные без интерактивной авторизации либо заранее загруженные в Docker; их совместимость подтверждает именно прогон.

Для короткой проверки без предыдущего релиза явно задайте `REAL_CITY_SKIP_ROLLBACK=1`: такой запуск отмечает откат как `skipped` и не является полной приёмкой. PR workflow использует этот режим; ручной `workflow_dispatch` требует оба предыдущих образа. Проверка восстановления backup выполняется отдельно от отката кода; сценарий несовместимой схемы и потерю данных после времени backup ещё нужно принять на стенде.

`/ready` проверяет PostgreSQL и возвращает 503 при остановленной или зависшей БД; production healthcheck использует этот endpoint. Проверка имеет бюджет одну секунду и допускает только один одновременно выполняющийся ping, даже если драйвер игнорирует отмену контекста. При зависании последующие `/ready` сразу возвращают 503; после восстановления БД следующий ping возвращает 200. Остальные игровые SQL-запросы имеют отдельные бюджеты и могут ждать дольше. `/health` остаётся проверкой HTTP-процесса. Сессии рабочего API хранятся в PostgreSQL вместе с игровыми данными.

Конфигурация: `docker-compose.production.yml`. PostgreSQL, Redis и API доступны только внутри сети Compose. Caddy обслуживает сборку клиента, проксирует HTTP и WebSocket `/api/*` и получает TLS-сертификат для `DOMAIN`. Требуются DNS-запись домена и доступные порты 80/443. Сервер симуляции встроен в API; отдельный worker одновременно с ним запускать нельзя.

## Подготовка образов

Из корня репозитория, после успешного CI:

```bash
docker build -t registry.example/real-city-backend:VERSION backend
docker build -f frontend/Dockerfile -t registry.example/real-city-frontend:VERSION .
```

Опубликуйте образы в своём registry. Скопируйте [`.env.prod.example`](../../.env.prod.example) в локальный `.env` на сервере и заполните `BACKEND_IMAGE`, `FRONTEND_IMAGE`, `DOMAIN`, `SESSION_SECRET`, `POSTGRES_PASSWORD`. Пустые значения шаблона намеренно не проходят `docker compose config`. Секрет сессий должен быть случайным, минимум 32 символа. Для пароля PostgreSQL используйте случайную строку из букв и цифр, поскольку она входит в URI соединения. Файл `.env` не хранится в Git. Фиксируйте версии образов, не используйте `latest`.

Необязательные переменные шаблона управляют HTTP/WS-таймаутами, размерами пула PostgreSQL и интервалом/параллелизмом симуляции. Значения по умолчанию совпадают с текущим runtime. `SERVER_SHUTDOWN_TIMEOUT=10s`, а Compose ждёт SIGTERM до 20 секунд; при изменении этих значений оставляйте запас на остановку. Проверяйте итог командой `docker compose -f docker-compose.production.yml config` без публикации результата с секретами.

## Первый запуск и обновление

```bash
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d postgres redis
docker compose -f docker-compose.production.yml run --rm backend /app/migrate up
docker compose -f docker-compose.production.yml up -d --wait
```

Перед обновлением сохраните предыдущие значения обоих образов, выполните резервное копирование и проверку восстановления. На время миграций остановите API командой `docker compose -f docker-compose.production.yml stop backend`. После запуска проверьте вход, карту, действие игрока, WebSocket-доставку второму игроку и отсутствие ошибок симуляции в логах. `/health` проверяет HTTP-процесс и не заменяет игровую приёмку или проверку БД.

## Резервные копии

```bash
bash scripts/backup-production.sh /srv/backups/real-city-2026-10-30.dump
bash scripts/verify-production-backup.sh /srv/backups/real-city-2026-10-30.dump
```

Первая команда атомарно публикует новый dump после проверки каталога архива, вторая выполняет настоящий restore в отдельный временный PostgreSQL и проверяет основные таблицы. Существующий файл копии не перезаписывается. Запланируйте ежедневный запуск внешним cron/systemd, храните минимум семь ежедневных копий и отдельную зашифрованную копию вне сервера. Секреты и настройки инфраструктуры сохраняйте отдельно. Redis используется для вспомогательных данных и координации; сессии рабочего API и авторитетные игровые данные восстанавливаются из PostgreSQL.

## Откат

Если миграции совместимы с предыдущим кодом, верните прежние `BACKEND_IMAGE`/`FRONTEND_IMAGE` и выполните `up -d --wait`. Автоматически откатывать миграции командой `down` нельзя: она может удалить игровые данные. Для несовместимого изменения остановите приложение, восстановите проверенный dump в новую БД, проверьте его и переключите приложение на неё. Изменения игроков после времени копии будут потеряны; заранее назначьте окно обслуживания. Исходный volume сохраняйте до приёмки восстановления.

Frontend/backend-образы, локальный TLS, proxy, миграции, backup/restore, игровой рестарт и штатная остановка API проверены в одноразовом production Compose. Откат на конкретные предыдущие образы, внешний TLS и целевой сервер остаются открытыми. Текущий объём проверок указан в [отчёте 101–110](../plans/queue-101-110-implementation.md).
