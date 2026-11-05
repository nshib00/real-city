-- +goose Up
ALTER TABLE buildings ADD COLUMN tower_watchkeeper_assigned BOOLEAN NOT NULL DEFAULT FALSE;

-- +goose Down
ALTER TABLE buildings DROP COLUMN IF EXISTS tower_watchkeeper_assigned;
