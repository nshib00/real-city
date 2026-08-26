-- +goose Up
UPDATE world_tiles
SET terrain = 'grass', updated_at = now()
WHERE terrain = 'stone';

-- +goose Down
-- Stone terrain is intentionally removed from the game; this migration is not reversible.
