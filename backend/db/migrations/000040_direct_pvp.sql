-- +goose Up
-- Отменяем старые отложенные атаки без применения урона.
DELETE FROM game_actions WHERE type = 'resolve_raid';
ALTER TABLE player_profiles RENAME COLUMN raid_alerts TO attack_alerts;
ALTER TABLE monsters ADD COLUMN creator_id text NOT NULL DEFAULT '';
ALTER TABLE monsters ADD COLUMN expires_at timestamptz;
CREATE INDEX monsters_creator_alive_idx ON monsters (creator_id, expires_at) WHERE state <> 'dead' AND creator_id <> '';
CREATE INDEX game_actions_actor_type_created_idx ON game_actions (actor_id, type, created_at);

-- +goose Down
DROP INDEX game_actions_actor_type_created_idx;
DROP INDEX monsters_creator_alive_idx;
ALTER TABLE monsters DROP COLUMN expires_at;
ALTER TABLE monsters DROP COLUMN creator_id;
ALTER TABLE player_profiles RENAME COLUMN attack_alerts TO raid_alerts;
