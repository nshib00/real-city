-- +goose Up
CREATE TABLE chat_moderation_audit(
 id text PRIMARY KEY,
 actor_id text NOT NULL,
 message_id text NOT NULL,
 action text NOT NULL CHECK(action IN ('approve','reject')),
 reason text NOT NULL,
 created_at timestamptz NOT NULL
);
CREATE INDEX idx_moderation_audit_created ON chat_moderation_audit(created_at DESC,id DESC);
CREATE INDEX idx_chat_flagged ON chat_messages(created_at,id) WHERE flagged;
-- +goose Down
DROP INDEX idx_chat_flagged;
DROP TABLE chat_moderation_audit;
