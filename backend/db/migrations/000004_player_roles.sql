-- +goose Up
ALTER TABLE players ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';

UPDATE players SET role = 'user' WHERE role = '';

-- +goose Down
SELECT 1;
