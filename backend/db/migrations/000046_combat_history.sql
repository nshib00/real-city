-- +goose Up
CREATE INDEX idx_combat_history_actor ON game_actions(actor_id,created_at DESC,id DESC) WHERE type='combat_record';
CREATE INDEX idx_combat_history_owner ON game_actions((payload->>'owner_id'),created_at DESC,id DESC) WHERE type='combat_record';
-- +goose Down
DROP INDEX idx_combat_history_owner;
DROP INDEX idx_combat_history_actor;
