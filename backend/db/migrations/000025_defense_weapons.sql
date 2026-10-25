-- +goose Up
CREATE INDEX IF NOT EXISTS idx_buildings_ready_defense_weapons
    ON buildings (map_id, cannon_next_attack_at, id)
    WHERE type IN ('defense_bolt_thrower', 'defense_storm_coil')
      AND cannon_enabled = TRUE AND state IN ('active', 'damaged');

-- +goose Down
DROP INDEX IF EXISTS idx_buildings_ready_defense_weapons;
