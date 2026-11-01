-- +goose Up
CREATE TABLE chat_reads (
 player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
 scope TEXT NOT NULL,
 read_at TIMESTAMPTZ NOT NULL,
 PRIMARY KEY(player_id,scope)
);
CREATE INDEX chat_alliance_history ON chat_messages(alliance_id,created_at DESC);
-- +goose Down
DROP TABLE chat_reads;
DROP INDEX chat_alliance_history;
