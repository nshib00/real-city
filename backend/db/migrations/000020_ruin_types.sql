-- +goose Up
ALTER TABLE world_tiles
    ADD COLUMN ruin_type TEXT NOT NULL DEFAULT '';

UPDATE world_tiles
SET ruin_type = (ARRAY[
    'ruins_town_square', 'ruins_archive', 'ruins_mint', 'ruins_storage',
    'ruins_greenhouse', 'ruins_water_station', 'ruins_bastion',
    'ruins_mechanic_workshop', 'ruins_wind_shrine', 'ruins_ore_obelisk',
    'ruins_rift_watch', 'ruins_river_lighthouse'
])[(abs(hashtext(map_id || ':' || tile_x || ':' || tile_y)::bigint) % 12 + 1)::int]
WHERE terrain = 'ruins' AND ruin_type = '';

UPDATE world_chunks AS chunk
SET version = version + 1, updated_at = now()
WHERE EXISTS (
    SELECT 1 FROM world_tiles AS tile
    WHERE tile.map_id = chunk.map_id
      AND tile.chunk_x = chunk.chunk_x
      AND tile.chunk_y = chunk.chunk_y
      AND tile.terrain = 'ruins'
);

-- +goose Down
ALTER TABLE world_tiles DROP COLUMN ruin_type;
