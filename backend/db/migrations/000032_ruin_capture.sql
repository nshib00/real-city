-- +goose Up
CREATE UNIQUE INDEX IF NOT EXISTS buildings_active_ruins_tile_unique
ON buildings (map_id, tile_x, tile_y)
WHERE type LIKE 'ruins_%' AND state <> 'ruined';

CREATE INDEX IF NOT EXISTS buildings_ruined_ruins_cleanup
ON buildings (updated_at, id)
WHERE type LIKE 'ruins_%' AND state = 'ruined';

-- +goose Down
DROP INDEX IF EXISTS buildings_ruined_ruins_cleanup;
DROP INDEX IF EXISTS buildings_active_ruins_tile_unique;
