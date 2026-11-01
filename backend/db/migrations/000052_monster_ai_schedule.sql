-- +goose Up
ALTER TABLE monsters ADD COLUMN next_ai_at timestamptz NOT NULL DEFAULT now();
CREATE INDEX idx_monsters_next_ai ON monsters (map_id, next_ai_at, id) WHERE state <> 'dead';

-- +goose Down
DROP INDEX idx_monsters_next_ai;
ALTER TABLE monsters DROP COLUMN next_ai_at;
