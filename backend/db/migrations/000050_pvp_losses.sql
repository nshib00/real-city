-- +goose Up
CREATE TABLE player_pvp_losses (
    player_id text PRIMARY KEY REFERENCES players(id), day timestamptz NOT NULL,
    damage integer NOT NULL CHECK(damage BETWEEN 0 AND 10000),
    destructions integer NOT NULL CHECK(destructions BETWEEN 0 AND 3)
);
-- +goose Down
DROP TABLE player_pvp_losses;
