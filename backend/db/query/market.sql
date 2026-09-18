-- name: CreateMarketOrder :exec
INSERT INTO market_orders (id, player_id, side, resource, amount, price, fee, status, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);

-- name: GetMarketOrder :one
SELECT id, player_id, side, resource, amount, price, fee, status, created_at, updated_at
FROM market_orders
WHERE id = $1;

-- name: UpdateMarketOrder :exec
UPDATE market_orders
SET status = $2, updated_at = $3
WHERE id = $1;

-- name: ListMarketOrders :many
SELECT id, player_id, side, resource, amount, price, fee, status, created_at, updated_at
FROM market_orders
WHERE status = $1
ORDER BY created_at DESC
LIMIT $2;
