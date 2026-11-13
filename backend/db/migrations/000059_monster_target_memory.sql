-- +goose Up
ALTER TABLE monsters ADD COLUMN target_tile_x INTEGER NOT NULL DEFAULT 0;
ALTER TABLE monsters ADD COLUMN target_tile_y INTEGER NOT NULL DEFAULT 0;
ALTER TABLE monsters ADD COLUMN target_last_seen_at TIMESTAMPTZ;

-- +goose Down
ALTER TABLE monsters DROP COLUMN IF EXISTS target_last_seen_at;
ALTER TABLE monsters DROP COLUMN IF EXISTS target_tile_y;
ALTER TABLE monsters DROP COLUMN IF EXISTS target_tile_x;
