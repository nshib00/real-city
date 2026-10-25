-- +goose Up
CREATE UNIQUE INDEX IF NOT EXISTS idx_buildings_one_oil_well_per_tile
    ON buildings (map_id, tile_x, tile_y)
    WHERE type = 'oil_well' AND state <> 'ruined';

CREATE UNIQUE INDEX IF NOT EXISTS idx_resource_nodes_one_active_oil_per_tile
    ON resource_nodes (map_id, tile_x, tile_y)
    WHERE resource = 'oil' AND state <> 'depleted';

-- +goose Down
DROP INDEX IF EXISTS idx_resource_nodes_one_active_oil_per_tile;
DROP INDEX IF EXISTS idx_buildings_one_oil_well_per_tile;
