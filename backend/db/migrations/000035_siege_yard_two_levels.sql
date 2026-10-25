-- +goose Up
-- Refund the old third-level upgrade before converting legacy yards. Already
-- paid production jobs keep their recipe ID and can finish normally.
WITH converted AS (
    SELECT owner_id, COUNT(*) AS quantity
    FROM buildings
    WHERE type = 'siege_yard' AND level > 2
    GROUP BY owner_id
)
INSERT INTO player_inventories (player_id, resource, amount, updated_at)
SELECT converted.owner_id, refund.resource, converted.quantity * refund.amount, now()
FROM converted
CROSS JOIN (VALUES
    ('coins', 1450000),
    ('reinforced_concrete', 30),
    ('electronics', 10),
    ('mechanism', 18)
) AS refund(resource, amount)
ON CONFLICT (player_id, resource) DO UPDATE
SET amount = player_inventories.amount + EXCLUDED.amount,
    updated_at = now();

UPDATE buildings
SET level = 2,
    health = LEAST(health, 3900),
    updated_at = now()
WHERE type = 'siege_yard' AND level > 2;

-- +goose Down
-- The original level of each converted building cannot be reconstructed safely.
SELECT 1;
