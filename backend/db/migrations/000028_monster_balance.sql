-- +goose Up
-- Preserve the current health percentage of monsters already living in the
-- persistent world when the catalog balance changes.
WITH balance(type, max_health, damage) AS (
    VALUES
        ('roaming_melee', 360, 18),
        ('resource_guardian', 560, 26),
        ('ruins_guardian', 840, 38),
        ('forest_stalker', 300, 14),
        ('spore_beast', 640, 22),
        ('ironback_brute', 1240, 44),
        ('ember_wisp', 480, 16),
        ('ancient_colossus', 300000, 2400)
)
UPDATE monsters AS m
SET max_health = balance.max_health,
    health = CASE WHEN m.state = 'dead' THEN 0
        ELSE LEAST(balance.max_health, GREATEST(1,
            ROUND(m.health::numeric * balance.max_health / GREATEST(m.max_health, 1))::integer)) END,
    damage = balance.damage
FROM balance
WHERE m.type = balance.type
  AND (m.max_health <> balance.max_health OR m.damage <> balance.damage);

-- +goose Down
-- Health changes to live monsters cannot be safely reversed after combat.
SELECT 1;
