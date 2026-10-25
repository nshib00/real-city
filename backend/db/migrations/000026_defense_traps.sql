-- +goose Up
ALTER TABLE buildings ADD COLUMN trap_charges INTEGER NOT NULL DEFAULT 0 CHECK (trap_charges >= 0);
CREATE UNIQUE INDEX IF NOT EXISTS idx_buildings_active_trap_tile
    ON buildings (map_id, tile_x, tile_y)
    WHERE type IN ('defense_stakes', 'defense_resin_snare') AND state <> 'ruined';

-- +goose Down
DROP INDEX IF EXISTS idx_buildings_active_trap_tile;
ALTER TABLE buildings DROP COLUMN IF EXISTS trap_charges;
