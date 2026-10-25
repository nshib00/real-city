-- +goose Up
CREATE TABLE IF NOT EXISTS game_balance_version (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    version integer NOT NULL CHECK (version > 0),
    applied_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO game_balance_version (singleton, version) VALUES (true, 1)
ON CONFLICT (singleton) DO NOTHING;

-- +goose Down
DROP TABLE IF EXISTS game_balance_version;
