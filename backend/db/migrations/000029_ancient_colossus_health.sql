-- +goose Up
-- Existing colossi keep the same health percentage after the catalog update.
UPDATE monsters
SET health = CASE WHEN state = 'dead' THEN 0
        ELSE LEAST(300000, GREATEST(1,
            ROUND(health::numeric * 300000 / GREATEST(max_health, 1))::integer)) END,
    max_health = 300000,
    damage = 2400
WHERE type = 'ancient_colossus'
  AND (max_health <> 300000 OR damage <> 2400);

-- +goose Down
-- Combat after the migration makes a proportional rollback unsafe.
SELECT 1;
