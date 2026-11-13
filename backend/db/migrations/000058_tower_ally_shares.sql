-- +goose Up
CREATE TABLE tower_signal_shares (
    tower_id TEXT PRIMARY KEY REFERENCES buildings(id) ON DELETE CASCADE,
    alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    version BIGINT NOT NULL DEFAULT 1,
    member_joined_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tower_alert_recipients
    ADD COLUMN scope TEXT NOT NULL DEFAULT 'owner' CHECK (scope IN ('owner','ally')),
    ADD COLUMN relay_tower_id TEXT,
    ADD COLUMN alliance_id TEXT,
    ADD COLUMN share_version BIGINT,
    ADD COLUMN recipient_joined_at TIMESTAMPTZ,
    ADD COLUMN delivered_at TIMESTAMPTZ,
    ADD COLUMN region_x INTEGER,
    ADD COLUMN region_y INTEGER;

-- +goose Down
ALTER TABLE tower_alert_recipients
    DROP COLUMN region_y,
    DROP COLUMN region_x,
    DROP COLUMN alliance_id,
    DROP COLUMN share_version,
    DROP COLUMN delivered_at,
    DROP COLUMN recipient_joined_at,
    DROP COLUMN relay_tower_id,
    DROP COLUMN scope;
DROP TABLE tower_signal_shares;
