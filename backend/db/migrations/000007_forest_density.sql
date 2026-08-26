-- +goose Up
ALTER TABLE world_tiles
ADD COLUMN IF NOT EXISTS forest_density INTEGER NOT NULL DEFAULT 0;

UPDATE world_tiles
SET forest_density = 3
WHERE terrain = 'forest' AND forest_density = 0;

-- +goose Down
ALTER TABLE world_tiles
DROP COLUMN IF EXISTS forest_density;

