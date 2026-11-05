-- +goose Up
CREATE TABLE tower_alert_scans (
    map_id TEXT PRIMARY KEY,
    next_generation BIGINT NOT NULL DEFAULT 0,
    applied_generation BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE tower_alert_state (
    map_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    monster_id TEXT NOT NULL,
    inside BOOLEAN NOT NULL DEFAULT FALSE,
    last_sent_at TIMESTAMPTZ,
    episode BIGINT NOT NULL DEFAULT 0,
    seen_generation BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (map_id, owner_id, monster_id)
);
CREATE INDEX idx_tower_alert_state_inside ON tower_alert_state(map_id) WHERE inside;

CREATE TABLE tower_alert_incidents (
    id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    monster_id TEXT NOT NULL,
    episode BIGINT NOT NULL,
    tower_id TEXT NOT NULL,
    monster_type TEXT NOT NULL,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    target_building_id TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL,
    UNIQUE (map_id, owner_id, monster_id, episode)
);

CREATE TABLE tower_alert_recipients (
    incident_id TEXT NOT NULL REFERENCES tower_alert_incidents(id) ON DELETE CASCADE,
    player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    detected_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (incident_id, player_id)
);
CREATE INDEX idx_tower_alert_recipients_history ON tower_alert_recipients(player_id, detected_at DESC, incident_id DESC);

-- +goose Down
DROP TABLE tower_alert_recipients;
DROP TABLE tower_alert_incidents;
DROP TABLE tower_alert_state;
DROP TABLE tower_alert_scans;
