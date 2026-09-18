-- +goose Up
CREATE TABLE IF NOT EXISTS monsters (
    id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL,
    type TEXT NOT NULL,
    state TEXT NOT NULL,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    home_tile_x INTEGER NOT NULL,
    home_tile_y INTEGER NOT NULL,
    target_id TEXT NOT NULL DEFAULT '',
    target_type TEXT NOT NULL DEFAULT '',
    health INTEGER NOT NULL,
    max_health INTEGER NOT NULL,
    damage INTEGER NOT NULL,
    speed_tiles INTEGER NOT NULL,
    aggro_radius INTEGER NOT NULL,
    attack_range INTEGER NOT NULL,
    attack_cooldown_ms INTEGER NOT NULL,
    next_attack_at TIMESTAMPTZ,
    last_moved_at TIMESTAMPTZ NOT NULL,
    loot_coins INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS monster_spawn_points (
    id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL,
    type TEXT NOT NULL,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    radius INTEGER NOT NULL,
    max_alive INTEGER NOT NULL,
    cooldown_ms INTEGER NOT NULL,
    next_spawn_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS monster_events (
    id TEXT PRIMARY KEY,
    monster_id TEXT NOT NULL,
    type TEXT NOT NULL,
    target_id TEXT NOT NULL DEFAULT '',
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_monsters_map_tile ON monsters(map_id, tile_x, tile_y);
CREATE INDEX IF NOT EXISTS idx_monsters_state ON monsters(state, updated_at);
CREATE INDEX IF NOT EXISTS idx_monster_spawns_due ON monster_spawn_points(map_id, next_spawn_at);
CREATE INDEX IF NOT EXISTS idx_monster_events_monster ON monster_events(monster_id, created_at);

INSERT INTO monsters (
    id, map_id, type, state, tile_x, tile_y, home_tile_x, home_tile_y,
    health, max_health, damage, speed_tiles, aggro_radius, attack_range,
    attack_cooldown_ms, last_moved_at, loot_coins
) VALUES
    ('monster_roamer_1', 'dev-world', 'roaming_melee', 'wandering', 10, -3, 10, -3, 90, 90, 8, 1, 5, 1, 8000, now(), 18),
    ('monster_resource_1', 'dev-world', 'resource_guardian', 'wandering', 14, 6, 14, 6, 140, 140, 12, 1, 4, 1, 10000, now(), 34),
    ('monster_ruins_1', 'dev-world', 'ruins_guardian', 'wandering', -8, 12, -8, 12, 210, 210, 18, 1, 6, 1, 12000, now(), 58)
ON CONFLICT (id) DO NOTHING;

INSERT INTO monster_spawn_points (
    id, map_id, type, tile_x, tile_y, radius, max_alive, cooldown_ms, next_spawn_at
) VALUES
    ('spawn_roamers', 'dev-world', 'roaming_melee', 6, -7, 8, 4, 600000, now() + interval '2 minutes'),
    ('spawn_ruins', 'dev-world', 'ruins_guardian', -8, 12, 4, 2, 1080000, now() + interval '4 minutes')
ON CONFLICT (id) DO NOTHING;

-- +goose Down
DROP TABLE IF EXISTS monster_events;
DROP TABLE IF EXISTS monster_spawn_points;
DROP TABLE IF EXISTS monsters;
