-- +goose Up
ALTER TABLE player_inventories
    ALTER COLUMN amount TYPE BIGINT;

-- +goose Down
ALTER TABLE player_inventories
    ALTER COLUMN amount TYPE INTEGER;
