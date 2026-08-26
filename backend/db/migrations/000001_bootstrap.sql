-- +goose Up
CREATE TABLE IF NOT EXISTS schema_migrations_bootstrap (
    id smallint PRIMARY KEY DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations_bootstrap (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;

-- +goose Down
DROP TABLE IF EXISTS schema_migrations_bootstrap;

