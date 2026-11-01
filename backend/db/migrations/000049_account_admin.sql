-- +goose Up
CREATE TABLE account_admin_audit (
    id text PRIMARY KEY, actor_id text NOT NULL REFERENCES players(id),
    player_id text NOT NULL REFERENCES players(id), status text NOT NULL, role text NOT NULL,
    previous_status text NOT NULL, previous_role text NOT NULL,
    reason text NOT NULL CHECK (char_length(reason) BETWEEN 3 AND 500),
    created_at timestamptz NOT NULL
);
CREATE INDEX account_admin_audit_time ON account_admin_audit(created_at DESC,id DESC);

-- +goose Down
DROP TABLE account_admin_audit;
