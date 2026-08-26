-- name: ListInventory :many
SELECT player_id, resource, amount, updated_at
FROM player_inventories
WHERE player_id = $1
ORDER BY resource;

-- name: UpsertInventoryItem :exec
INSERT INTO player_inventories (player_id, resource, amount, updated_at)
VALUES ($1, $2, $3, now())
ON CONFLICT (player_id, resource)
DO UPDATE SET amount = EXCLUDED.amount, updated_at = EXCLUDED.updated_at;

-- name: InsertEconomyTransaction :exec
INSERT INTO economy_transactions (id, player_id, kind, resource, amount, reason, created_at)
VALUES ($1, $2, $3, $4, $5, $6, $7);

-- name: ListResourceNodes :many
SELECT id, map_id, type, resource, amount, max_amount, state, owner_id, tile_x, tile_y, respawn_at, created_at, updated_at
FROM resource_nodes
WHERE map_id = $1;

-- name: UpsertResourceNode :exec
INSERT INTO resource_nodes (id, map_id, type, resource, amount, max_amount, state, owner_id, tile_x, tile_y, respawn_at, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, NULLIF($8, ''), $9, $10, $11, $12, $13)
ON CONFLICT (id)
DO UPDATE SET amount = EXCLUDED.amount, state = EXCLUDED.state, owner_id = EXCLUDED.owner_id, respawn_at = EXCLUDED.respawn_at, updated_at = EXCLUDED.updated_at;

-- name: ListProductionJobs :many
SELECT id, player_id, building_id, recipe_id, state, started_at, completes_at, created_at, updated_at
FROM production_jobs
WHERE player_id = $1
ORDER BY created_at DESC;

-- name: UpsertProductionJob :exec
INSERT INTO production_jobs (id, player_id, building_id, recipe_id, state, started_at, completes_at, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
ON CONFLICT (id)
DO UPDATE SET state = EXCLUDED.state, updated_at = EXCLUDED.updated_at;

