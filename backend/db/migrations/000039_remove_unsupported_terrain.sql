-- +goose Up
-- Старые типы без игровых моделей выглядят как луг, но сохраняют чужие правила размещения.
UPDATE world_tiles
SET terrain = 'grass', ruin_type = '', forest_density = 0, updated_at = now()
WHERE terrain NOT IN ('grass', 'forest', 'water', 'mountain', 'road', 'oil_well', 'ruins');

-- +goose Down
-- Исходные типы удалённых клеток восстановить невозможно.
