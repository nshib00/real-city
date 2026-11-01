-- +goose Up
CREATE TABLE repair_jobs (
 id TEXT PRIMARY KEY,
 building_id TEXT NOT NULL,
 player_id TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
 building_type TEXT NOT NULL,
 level INTEGER NOT NULL CHECK(level>0),
 workers INTEGER NOT NULL CHECK(workers>0),
 due_at TIMESTAMPTZ NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','completed','cancelled'))
);
CREATE UNIQUE INDEX repair_one_pending ON repair_jobs(building_id) WHERE status='pending';
CREATE INDEX repair_due ON repair_jobs(due_at) WHERE status='pending';
-- +goose Down
DROP TABLE repair_jobs;
