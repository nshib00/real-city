-- name: GetWorldMap
SELECT id, name, seed, chunk_size, spawn_radius
FROM world_maps
WHERE id = $1;

-- name: GetWorldChunk
SELECT version
FROM world_chunks
WHERE map_id = $1 AND chunk_x = $2 AND chunk_y = $3;

-- name: ListWorldTilesByChunk
SELECT tile_x, tile_y, terrain, elevation, safe_zone
FROM world_tiles
WHERE map_id = $1 AND chunk_x = $2 AND chunk_y = $3
ORDER BY tile_y, tile_x;
