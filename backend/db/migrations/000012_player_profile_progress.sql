-- +goose Up
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS city_name TEXT NOT NULL DEFAULT '';
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS level INTEGER NOT NULL DEFAULT 1;
ALTER TABLE player_profiles ADD COLUMN IF NOT EXISTS xp INTEGER NOT NULL DEFAULT 0;

UPDATE player_profiles
SET city_name = display_name
WHERE city_name = '';

-- +goose Down
ALTER TABLE player_profiles DROP COLUMN IF EXISTS xp;
ALTER TABLE player_profiles DROP COLUMN IF EXISTS level;
ALTER TABLE player_profiles DROP COLUMN IF EXISTS city_name;
