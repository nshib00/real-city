-- +goose Up
-- Counts of pending and dead items can use narrow partial indexes during 30s sampling.
CREATE INDEX IF NOT EXISTS idx_observability_actions_pending_due ON game_actions (due_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_observability_outbox_pending_due ON outbox_events (next_attempt_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_observability_outbox_dead ON outbox_events (status) WHERE status = 'dead';
CREATE INDEX IF NOT EXISTS idx_observability_buildings_due ON buildings (completes_at) WHERE state = 'building' AND completes_at IS NOT NULL;
-- Production already has idx_production_jobs_due(state, completes_at).

-- +goose Down
DROP INDEX IF EXISTS idx_observability_buildings_due;
DROP INDEX IF EXISTS idx_observability_outbox_dead;
DROP INDEX IF EXISTS idx_observability_outbox_pending_due;
DROP INDEX IF EXISTS idx_observability_actions_pending_due;
