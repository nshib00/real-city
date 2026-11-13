-- +goose Up
ALTER TABLE monster_spawn_points
    ADD COLUMN IF NOT EXISTS warning_at TIMESTAMPTZ;

-- +goose Down
ALTER TABLE monster_spawn_points
    DROP COLUMN IF EXISTS warning_at;
