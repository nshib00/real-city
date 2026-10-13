-- +goose Up
UPDATE monsters
SET max_health = 180, health = LEAST(GREATEST(health, 1), 180), damage = 18, speed_tiles = 1,
    aggro_radius = 5, attack_range = 1, attack_cooldown_ms = 8000, loot_coins = 65
WHERE type = 'roaming_melee';

UPDATE monsters
SET max_health = 280, health = LEAST(GREATEST(health, 1), 280), damage = 26, speed_tiles = 1,
    aggro_radius = 4, attack_range = 1, attack_cooldown_ms = 10000, loot_coins = 120
WHERE type = 'resource_guardian';

UPDATE monsters
SET max_health = 420, health = LEAST(GREATEST(health, 1), 420), damage = 38, speed_tiles = 1,
    aggro_radius = 6, attack_range = 1, attack_cooldown_ms = 12000, loot_coins = 220
WHERE type = 'ruins_guardian';

-- +goose Down
UPDATE monsters
SET max_health = 90, health = LEAST(GREATEST(health, 1), 90), damage = 8, speed_tiles = 1,
    aggro_radius = 5, attack_range = 1, attack_cooldown_ms = 8000, loot_coins = 18
WHERE type = 'roaming_melee';

UPDATE monsters
SET max_health = 140, health = LEAST(GREATEST(health, 1), 140), damage = 12, speed_tiles = 1,
    aggro_radius = 4, attack_range = 1, attack_cooldown_ms = 10000, loot_coins = 34
WHERE type = 'resource_guardian';

UPDATE monsters
SET max_health = 210, health = LEAST(GREATEST(health, 1), 210), damage = 18, speed_tiles = 1,
    aggro_radius = 6, attack_range = 1, attack_cooldown_ms = 12000, loot_coins = 58
WHERE type = 'ruins_guardian';
