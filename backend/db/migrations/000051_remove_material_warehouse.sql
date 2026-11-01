-- +goose Up
DELETE FROM buildings WHERE type = 'warehouse';

-- +goose Down
-- Удалённые склады и связанные задания невозможно восстановить без резервной копии.
