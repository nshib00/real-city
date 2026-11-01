-- +goose Up
DROP INDEX IF EXISTS idx_monsters_tick;

-- +goose Down
CREATE INDEX IF NOT EXISTS idx_monsters_tick
    ON monsters(map_id, state, updated_at, id)
    WHERE state <> 'dead';
