-- +goose Up
ALTER TABLE player_profiles ADD COLUMN avatar_id TEXT NOT NULL DEFAULT '',ADD COLUMN banner_id TEXT NOT NULL DEFAULT '',ADD COLUMN title TEXT NOT NULL DEFAULT '',ADD COLUMN home_center_id TEXT NOT NULL DEFAULT '';
-- +goose Down
ALTER TABLE player_profiles DROP COLUMN avatar_id,DROP COLUMN banner_id,DROP COLUMN title,DROP COLUMN home_center_id;
