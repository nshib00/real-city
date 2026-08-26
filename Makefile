COMPOSE := docker compose -f docker-compose.yml -f docker-compose.dev.yml
POSTGRES_DSN ?= postgres://real_city:real_city@postgres:5432/real_city?sslmode=disable

.PHONY: test backend-test frontend-test backend-run backend-up backend-down \
 backend-logs backend-run-local db-up \
 migrate-up migrate-down migrate-status \
 create-test-admin frontend-dev

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

db-up:
	docker compose up -d postgres redis

migrate-up: db-up
	$(COMPOSE) run --rm --build -e POSTGRES_DSN="$(POSTGRES_DSN)" backend /app/migrate up

migrate-down: db-up
	$(COMPOSE) run --rm --build -e POSTGRES_DSN="$(POSTGRES_DSN)" backend /app/migrate down

migrate-status: db-up
	$(COMPOSE) run --rm --build -e POSTGRES_DSN="$(POSTGRES_DSN)" backend /app/migrate status

create-test-admin:
	POSTGRES_DSN="$(POSTGRES_DSN)" ./scripts/create-test-admin.sh

backend-run-local:
	cd backend && go run ./cmd/api

frontend-dev:
	cd frontend && npm run dev -- --host 0.0.0.0
