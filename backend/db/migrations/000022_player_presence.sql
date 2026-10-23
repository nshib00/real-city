-- +goose Up
CREATE TABLE player_presence (
    player_id text PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
    tile_x integer NOT NULL CHECK (tile_x BETWEEN 0 AND 159),
    tile_y integer NOT NULL CHECK (tile_y BETWEEN 0 AND 159),
    updated_at timestamptz NOT NULL
);

CREATE INDEX player_presence_updated_at_idx ON player_presence (updated_at);

-- +goose Down
DROP TABLE player_presence;
