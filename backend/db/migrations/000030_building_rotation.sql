-- +goose Up
ALTER TABLE buildings ADD COLUMN rotation SMALLINT NOT NULL DEFAULT 0 CHECK (rotation BETWEEN 0 AND 3);

-- +goose Down
ALTER TABLE buildings DROP COLUMN rotation;
