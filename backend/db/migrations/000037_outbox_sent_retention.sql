-- +goose Up
CREATE INDEX IF NOT EXISTS idx_outbox_sent_updated_at ON outbox_events (updated_at, id) WHERE status = 'sent';

-- +goose Down
DROP INDEX IF EXISTS idx_outbox_sent_updated_at;
