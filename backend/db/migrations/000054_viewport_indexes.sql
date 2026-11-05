-- +goose Up
CREATE INDEX IF NOT EXISTS idx_monsters_viewport_alive
    ON monsters(map_id, tile_x, tile_y) WHERE state <> 'dead';

-- +goose Down
DROP INDEX IF EXISTS idx_monsters_viewport_alive;
