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

UPDATE monster_spawn_points
SET max_alive = 1, cooldown_ms = 90000
WHERE id IN ('spawn_roamers', 'spawn_ruins');

INSERT INTO monster_spawn_points (
    id, map_id, type, tile_x, tile_y, radius, max_alive, cooldown_ms, next_spawn_at
) VALUES
    ('spawn_resources', 'dev-world', 'resource_guardian', 14, 6, 6, 1, 90000, now() + interval '1 minute'),
    ('spawn_north_forest', 'dev-world', 'roaming_melee', -16, -18, 8, 1, 90000, now() + interval '90 seconds'),
    ('spawn_east_grove', 'dev-world', 'roaming_melee', 24, -9, 8, 1, 90000, now() + interval '100 seconds'),
    ('spawn_south_meadow', 'dev-world', 'roaming_melee', 8, 22, 8, 1, 90000, now() + interval '110 seconds'),
    ('spawn_west_ruins', 'dev-world', 'ruins_guardian', -24, 8, 6, 1, 90000, now() + interval '120 seconds'),
    ('spawn_far_north', 'dev-world', 'resource_guardian', 3, -29, 8, 1, 90000, now() + interval '130 seconds'),
    ('spawn_far_east', 'dev-world', 'roaming_melee', 31, 13, 8, 1, 90000, now() + interval '140 seconds'),
    ('spawn_far_south', 'dev-world', 'resource_guardian', -11, 30, 8, 1, 90000, now() + interval '150 seconds')
ON CONFLICT (id) DO NOTHING;

-- +goose Down
DROP TABLE IF EXISTS monster_loot_drops;
ALTER TABLE monsters DROP COLUMN IF EXISTS spawn_id;
