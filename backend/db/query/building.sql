-- name: list_player_buildings
SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y, footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at, field_stage_ready_at, field_super_crop, created_at, updated_at
FROM buildings
WHERE owner_id = $1
ORDER BY created_at, id;

-- name: list_chunk_buildings
SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y, footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at, field_stage_ready_at, field_super_crop, created_at, updated_at
FROM buildings
WHERE map_id = $1
  AND tile_x >= $2 AND tile_x < $3
  AND tile_y >= $4 AND tile_y < $5
ORDER BY tile_y, tile_x, created_at;

-- name: find_building
SELECT id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y, footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at, field_stage_ready_at, field_super_crop, created_at, updated_at
FROM buildings
WHERE id = $1;

-- name: insert_building
INSERT INTO buildings (id, map_id, owner_id, type, name, level, state, health, tile_x, tile_y, footprint_w, footprint_h, started_at, completes_at, field_stage, field_stage_started_at, field_stage_ready_at, field_super_crop, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20);

-- name: update_building
UPDATE buildings
SET type = $2, name = $3, level = $4, state = $5, health = $6, completes_at = $7, updated_at = $8
WHERE id = $1;

-- name: delete_building
DELETE FROM buildings
WHERE id = $1;
