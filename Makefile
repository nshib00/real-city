COMPOSE := docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_OBSERVABILITY := $(COMPOSE) -f docker-compose.observability.yml
COMPOSE_PRODUCTION_BUILD := docker compose -f docker-compose.production.yml -f docker-compose.production-build.yml
COMPOSE_TEST := docker compose -p real-city-test -f docker-compose.test.yml
COMPOSE_TEST_OBSERVABILITY := $(COMPOSE_TEST) -f docker-compose.observability.yml
COMPOSE_LAPTOP := $(COMPOSE_TEST) -f docker-compose.laptop.yml
POSTGRES_DSN ?= postgres://real_city:real_city@postgres:5432/real_city?sslmode=disable
TEST_POSTGRES_DSN ?= postgres://real_city:real_city@postgres:5432/real_city?sslmode=disable
BLENDER ?= blender

.PHONY: test backend-test frontend-test backend-prod-up frontend-prod-up backend-prod-down frontend-prod-down backend-dev-up backend-dev-down backend-local-up frontend-dev-up frontend-test-up backend-test-up backend-test-down backend-laptop-up backend-laptop-down catalog-check \
	migrate-production \
	 backend-logs db-up \
 migrate-up migrate-down migrate-status \
	 test-backend-logs test-db-up \
 test-migrate-up test-migrate-down test-migrate-status \
	 create-test-admin \
	 backend-observability-up backend-observability-down observability-targets observability-logs \
	 backend-test-observability-up backend-test-observability-down test-observability-logs \
 asset-pipeline-smoke asset-pipeline-local asset-contact-sheets asset-pipeline-blender-roundtrip

test: backend-test frontend-test

catalog-check:
	python3 tools/player/generate_levels.py --check
	python3 tools/buildings/check_balance_snapshot.py
	python3 docs/buildings/audit-catalogs.py
	python3 docs/buildings/check-coverage.py
	python3 docs/buildings/sync-runtime-tables.py --check
	python3 docs/buildings/sync-xp-tables.py --check
	cmp data/balance/v2.json backend/internal/domain/catalog/balance.v2.json
	cd backend && GOCACHE=/tmp/real-city-go-cache go test ./internal/domain/catalog

backend-test:
	cd backend && GOCACHE=/tmp/real-city-go-cache go test ./...

frontend-test:
	cd frontend && npm test

# Build the production backend image and start the backend services.
backend-prod-up:
	$(COMPOSE_PRODUCTION_BUILD) build backend
	$(COMPOSE_PRODUCTION_BUILD) up -d --wait postgres redis
	$(MAKE) migrate-production
	$(COMPOSE_PRODUCTION_BUILD) up -d --wait backend

migrate-production:
	$(COMPOSE_PRODUCTION_BUILD) up -d --wait postgres redis
	$(COMPOSE_PRODUCTION_BUILD) run --rm --no-deps backend /app/migrate up

frontend-prod-up:
	$(COMPOSE_PRODUCTION_BUILD) build web
	$(COMPOSE_PRODUCTION_BUILD) up -d --wait

backend-prod-down:
	$(COMPOSE_PRODUCTION_BUILD) stop backend postgres redis

frontend-prod-down:
	$(COMPOSE_PRODUCTION_BUILD) stop web backend postgres redis

backend-dev-up: migrate-up
	$(COMPOSE) up --build backend

backend-dev-down:
	$(COMPOSE) down

backend-logs:
	$(COMPOSE) logs -f backend

backend-observability-up: migrate-up
	$(COMPOSE_OBSERVABILITY) up -d --build --wait --wait-timeout 120 backend prometheus grafana

backend-observability-down:
	$(COMPOSE_OBSERVABILITY) stop grafana prometheus

observability-targets:
	curl --fail --silent --show-error 'http://127.0.0.1:9090/api/v1/targets?state=active' | python3 -m json.tool

observability-logs:
	$(COMPOSE_OBSERVABILITY) logs -f prometheus grafana

backend-test-observability-up: backend-test-up
	$(COMPOSE_TEST_OBSERVABILITY) up -d --build --wait --wait-timeout 120 prometheus grafana

backend-test-observability-down:
	$(COMPOSE_TEST_OBSERVABILITY) stop grafana prometheus

test-observability-logs:
	$(COMPOSE_TEST_OBSERVABILITY) logs -f prometheus grafana

db-up:
	docker compose up -d postgres redis

migrate-up: db-up
	$(COMPOSE) run --rm --build -e POSTGRES_DSN="$(POSTGRES_DSN)" backend /app/migrate up

migrate-down: db-up
	$(COMPOSE) run --rm --build -e POSTGRES_DSN="$(POSTGRES_DSN)" backend /app/migrate down

migrate-status: db-up
	$(COMPOSE) run --rm --build -e POSTGRES_DSN="$(POSTGRES_DSN)" backend /app/migrate status

test-db-up:
	$(COMPOSE_TEST) up -d postgres redis

test-migrate-up: test-db-up
	$(COMPOSE_TEST) run --rm --build -e POSTGRES_DSN="$(TEST_POSTGRES_DSN)" backend /app/migrate up

test-migrate-down: test-db-up
	$(COMPOSE_TEST) run --rm --build -e POSTGRES_DSN="$(TEST_POSTGRES_DSN)" backend /app/migrate down

test-migrate-status: test-db-up
	$(COMPOSE_TEST) run --rm --build -e POSTGRES_DSN="$(TEST_POSTGRES_DSN)" backend /app/migrate status

backend-test-up: test-migrate-up
	$(COMPOSE_TEST) up -d --build backend

backend-test-down:
	$(COMPOSE_TEST) down

test-backend-logs:
	$(COMPOSE_TEST) logs -f backend

create-test-admin: test-migrate-up
	./scripts/create-test-admin.sh

backend-local-up:
	cd backend && go run ./cmd/api

frontend-dev-up:
	cd frontend && npm run dev -- --host 0.0.0.0

frontend-test-up:
	cd frontend && VITE_API_PROXY_TARGET=http://localhost:18080 npm run dev -- --host 0.0.0.0

asset-pipeline-smoke:
	PYTHONPATH=tools/assets python3 -B tools/assets/validate_asset_specs.py
	PYTHONPATH=tools/assets python3 -B tools/assets/validate_building_manifests.py --skip-glb-header
	PYTHONPATH=tools/assets python3 -B tools/assets/validate_building_sprites.py --report /tmp/real-city-sprite-validation.json
	PYTHONPATH=tools/assets python3 -B tools/assets/validate_building_lods.py --allow-planned

asset-contact-sheets:
	PYTHONPATH=tools/assets python3 -B tools/assets/make_asset_contact_sheet.py --preview

asset-pipeline-blender-roundtrip:
	PYTHONPATH=tools/assets $(BLENDER) --background --python tools/assets/blender/validate_glb_roundtrip.py -- --limit 48 --report /tmp/real-city-glb-roundtrip.json

asset-pipeline-local: asset-pipeline-smoke asset-contact-sheets asset-pipeline-blender-roundtrip
	PYTHONPATH=tools/assets python3 -B tools/assets/validate_building_manifests.py
	PYTHONPATH=tools/assets python3 -B tools/assets/validate_building_ground.py

.PHONY: gameplay-restart-test
gameplay-restart-test:
	bash scripts/test-gameplay-restart.sh

.PHONY: contracts-check contracts-generate
contracts-check:
	bash scripts/check-contracts.sh
contracts-generate:
	python3 tools/sync_api_contracts.py

.PHONY: laptop-build backend-laptop-up backend-laptop-down laptop-config laptop-measure
laptop-build:
	$(COMPOSE_LAPTOP) --parallel 1 build backend frontend

# Сборка вынесена отдельно: обычный запуск не запускает компиляторы.
backend-laptop-up:
	$(COMPOSE_LAPTOP) stop frontend backend
	$(COMPOSE_LAPTOP) up -d --no-build --wait postgres redis
	$(COMPOSE_LAPTOP) run --rm --no-deps backend /app/migrate up
	$(COMPOSE_LAPTOP) exec -T postgres psql -X -U real_city -d real_city -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS pg_stat_statements'
	$(COMPOSE_LAPTOP) up -d --no-build backend frontend

backend-laptop-down:
	$(COMPOSE_LAPTOP) stop frontend backend redis postgres

laptop-config:
	$(COMPOSE_LAPTOP) config --quiet

laptop-measure:
	bash scripts/measure-laptop-resources.sh
