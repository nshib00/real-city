-- +goose Up
ALTER TABLE monsters ADD COLUMN shock_until TIMESTAMPTZ;

-- +goose Down
ALTER TABLE monsters DROP COLUMN IF EXISTS shock_until;
