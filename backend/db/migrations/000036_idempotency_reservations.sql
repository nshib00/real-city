-- +goose Up
ALTER TABLE http_idempotency_responses
ADD COLUMN IF NOT EXISTS state text NOT NULL DEFAULT 'completed'
CHECK (state IN ('pending', 'completed'));

-- +goose Down
ALTER TABLE http_idempotency_responses DROP COLUMN IF EXISTS state;
