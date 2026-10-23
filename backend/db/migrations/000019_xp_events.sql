-- +goose Up
CREATE TABLE player_xp_events (
    event_key TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES players(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_player_xp_events_player_created ON player_xp_events(player_id, created_at DESC);

-- +goose Down
DROP TABLE player_xp_events;
