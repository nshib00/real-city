-- +goose Up
WITH admin_player AS (
    SELECT id
    FROM players
    WHERE email = 'admin.test@real-city.local'
       OR email = 'admin@example.com'
),
resources(resource) AS (
    VALUES
        ('coins'),
        ('population'),
        ('aeolian-crystal'),
        ('wood'),
        ('stone'),
        ('clay'),
        ('sand'),
        ('coal'),
        ('iron_ore'),
        ('copper'),
        ('resin'),
        ('flax'),
        ('windleaf'),
        ('herbs'),
        ('mushrooms'),
        ('seeds'),
        ('brick'),
        ('stone_block'),
        ('metal'),
        ('iron'),
        ('steel'),
        ('glass'),
        ('planks'),
        ('premium_planks'),
        ('rope'),
        ('copper_parts'),
        ('iron_ingot'),
        ('gold_ingot'),
        ('cement'),
        ('concrete'),
        ('reinforced_concrete'),
        ('fabric'),
        ('mechanism'),
        ('super_mechanism'),
        ('electronics'),
        ('sulfur'),
        ('explosives'),
        ('oil'),
        ('fuel'),
        ('super-seeds'),
        ('super-fiber'),
        ('super-mushrooms'),
        ('super-windleaf'),
        ('emerald_dust'),
        ('elderwood-heart'),
        ('rune_tile')
)
INSERT INTO player_inventories (player_id, resource, amount, updated_at)
SELECT admin_player.id, resources.resource, 2000000000, now()
FROM admin_player
CROSS JOIN resources
ON CONFLICT (player_id, resource)
DO UPDATE SET amount = GREATEST(player_inventories.amount, EXCLUDED.amount),
              updated_at = EXCLUDED.updated_at;

-- +goose Down
-- Test-account resource backfills are intentionally not reverted.
