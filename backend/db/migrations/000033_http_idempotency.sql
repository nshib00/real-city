-- +goose Up
CREATE TABLE IF NOT EXISTS http_idempotency_responses (
    key_hash text PRIMARY KEY,
    fingerprint text NOT NULL,
    status integer NOT NULL,
    headers jsonb NOT NULL,
    body bytea NOT NULL,
    expires_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS http_idempotency_expires_idx ON http_idempotency_responses (expires_at);

-- +goose Down
DROP TABLE IF EXISTS http_idempotency_responses;
