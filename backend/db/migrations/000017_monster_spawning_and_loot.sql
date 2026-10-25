-- +goose Up
ALTER TABLE monsters
    ADD COLUMN IF NOT EXISTS spawn_id TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS monster_loot_drops (
    id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL,
    monster_id TEXT NOT NULL,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    claimed_by TEXT NOT NULL DEFAULT '',
    claimed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_monster_loot_viewport
    ON monster_loot_drops(map_id, tile_x, tile_y)
    WHERE claimed_by = '';

UPDATE monsters SET spawn_id = 'spawn_roamers' WHERE id = 'monster_roamer_1' AND spawn_id = '';
UPDATE monsters SET spawn_id = 'spawn_resources' WHERE id = 'monster_resource_1' AND spawn_id = '';
UPDATE monsters SET spawn_id = 'spawn_ruins' WHERE id = 'monster_ruins_1' AND spawn_id = '';

-- +goose Down
DROP TABLE IF EXISTS monster_loot_drops;
ALTER TABLE monsters DROP COLUMN IF EXISTS spawn_id;
