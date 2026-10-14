-- +goose Up
CREATE INDEX IF NOT EXISTS idx_monsters_tick
    ON monsters(map_id, state, updated_at, id)
    WHERE state <> 'dead';

CREATE INDEX IF NOT EXISTS idx_monsters_spawn_alive
    ON monsters(map_id, spawn_id)
    WHERE state <> 'dead' AND spawn_id <> '';

CREATE INDEX IF NOT EXISTS idx_buildings_viewport
    ON buildings(map_id, tile_x, tile_y, footprint_w, footprint_h);

CREATE INDEX IF NOT EXISTS idx_buildings_owner_limit_stats
    ON buildings(owner_id, state, type, level);

-- +goose Down
DROP INDEX IF EXISTS idx_buildings_owner_limit_stats;
DROP INDEX IF EXISTS idx_buildings_viewport;
DROP INDEX IF EXISTS idx_monsters_spawn_alive;
DROP INDEX IF EXISTS idx_monsters_tick;
