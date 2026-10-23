COMPOSE := docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_OBSERVABILITY := $(COMPOSE) -f docker-compose.observability.yml
COMPOSE_TEST := docker compose -p real-city-test -f docker-compose.test.yml
POSTGRES_DSN ?= postgres://real_city:real_city@postgres:5432/real_city?sslmode=disable
TEST_POSTGRES_DSN ?= postgres://real_city:real_city@postgres:5432/real_city?sslmode=disable
BLENDER ?= blender

.PHONY: test backend-test frontend-test backend-run backend-up backend-down \
 backend-logs backend-run-local db-up \
 migrate-up migrate-down migrate-status \
 test-backend-up test-backend-down test-backend-logs test-db-up \
 test-migrate-up test-migrate-down test-migrate-status \
 create-test-admin frontend-dev frontend-dev-test \
 observability-up observability-down observability-targets observability-logs \
 asset-pipeline-smoke asset-pipeline-local asset-contact-sheets asset-pipeline-blender-roundtrip

test: backend-test frontend-test

backend-test:
	cd backend && GOCACHE=/tmp/real-city-go-cache go test ./...

frontend-test:
	cd frontend && npm test

backend-run: backend-up

backend-up: migrate-up
	$(COMPOSE) up --build backend

backend-down:
	$(COMPOSE) down

backend-logs:
	$(COMPOSE) logs -f backend

observability-up: migrate-up
	$(COMPOSE_OBSERVABILITY) up -d --build --wait --wait-timeout 120 backend prometheus grafana

observability-down:
	$(COMPOSE_OBSERVABILITY) stop grafana prometheus

observability-targets:
	curl --fail --silent --show-error 'http://127.0.0.1:9090/api/v1/targets?state=active' | python3 -m json.tool

observability-logs:
	$(COMPOSE_OBSERVABILITY) logs -f prometheus grafana

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

test-backend-up: test-migrate-up
	$(COMPOSE_TEST) up -d --build backend

test-backend-down:
	$(COMPOSE_TEST) down

test-backend-logs:
	$(COMPOSE_TEST) logs -f backend

create-test-admin: test-migrate-up
	./scripts/create-test-admin.sh

backend-run-local:
	cd backend && go run ./cmd/api

frontend-dev:
	cd frontend && npm run dev -- --host 0.0.0.0

frontend-dev-test:
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
