-- +goose Up
CREATE TABLE tower_alert_relays (
    incident_id TEXT NOT NULL REFERENCES tower_alert_incidents(id) ON DELETE CASCADE,
    tower_id TEXT NOT NULL,
    PRIMARY KEY (incident_id, tower_id)
);

-- +goose Down
DROP TABLE tower_alert_relays;
