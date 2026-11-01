-- +goose Up
ALTER TABLE chat_messages ADD COLUMN audience jsonb NOT NULL DEFAULT '[]'::jsonb;
CREATE INDEX idx_chat_nearby_audience ON chat_messages USING gin(audience) WHERE channel='nearby';
CREATE INDEX idx_chat_channel_cursor ON chat_messages(channel,created_at DESC,id DESC);

-- +goose Down
DROP INDEX idx_chat_channel_cursor;
DROP INDEX idx_chat_nearby_audience;
ALTER TABLE chat_messages DROP COLUMN audience;
