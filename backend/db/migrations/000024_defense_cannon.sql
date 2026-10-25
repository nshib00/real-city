-- +goose Up
ALTER TABLE buildings
    ADD COLUMN cannon_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN cannon_next_attack_at TIMESTAMPTZ,
    ADD COLUMN cannon_target_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_buildings_ready_cannon
    ON buildings (map_id, cannon_next_attack_at, id)
    WHERE type = 'defense_cannon' AND cannon_enabled = TRUE AND state IN ('active', 'damaged');

-- +goose Down
DROP INDEX IF EXISTS idx_buildings_ready_cannon;
ALTER TABLE buildings
    DROP COLUMN IF EXISTS cannon_target_id,
    DROP COLUMN IF EXISTS cannon_next_attack_at,
    DROP COLUMN IF EXISTS cannon_enabled;
