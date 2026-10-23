package postgres

import (
	"context"
	"database/sql"
	"log/slog"
	"time"

	"real-city/backend/internal/observability"
)

// The four queries run at most once per 30 seconds, outside the HTTP scrape path.
// All predicates use fixed status values and indexed (status, due time) columns.
var queueQueries = []struct{ name, query, state string }{
	{"actions", `SELECT count(*), count(*) FILTER (WHERE due_at <= $2), min(due_at) FILTER (WHERE due_at <= $2), 0
		FROM game_actions WHERE status = $1`, "pending"},
	{"outbox", `SELECT count(*) FILTER (WHERE status = $1), count(*) FILTER (WHERE status = $1 AND next_attempt_at <= $2),
		min(next_attempt_at) FILTER (WHERE status = $1 AND next_attempt_at <= $2), count(*) FILTER (WHERE status = 'dead')
		FROM outbox_events WHERE status IN ($1, 'dead')`, "pending"},
	{"buildings", `SELECT count(*), count(*) FILTER (WHERE completes_at <= $2), min(completes_at) FILTER (WHERE completes_at <= $2), 0
		FROM buildings WHERE state = $1 AND completes_at IS NOT NULL`, "building"},
	{"production", `SELECT count(*), count(*) FILTER (WHERE completes_at <= $2), min(completes_at) FILTER (WHERE completes_at <= $2), 0
		FROM production_jobs WHERE state = $1`, "running"},
}

func CollectQueues(ctx context.Context, db *sql.DB, now time.Time) (map[string]observability.QueueState, error) {
	values := make(map[string]observability.QueueState, len(queueQueries))
	for _, q := range queueQueries {
		var v observability.QueueState
		var oldest sql.NullTime
		if err := db.QueryRowContext(ctx, q.query, q.state, now).Scan(&v.Pending, &v.Due, &oldest, &v.Dead); err != nil {
			return nil, err
		}
		if oldest.Valid {
			v.OldestDueAge = max(0, now.Sub(oldest.Time).Seconds())
		}
		values[q.name] = v
	}
	return values, nil
}

func RunQueueSampler(ctx context.Context, db *sql.DB, log *slog.Logger) {
	if db == nil {
		return
	}
	collect := func() {
		sampleCtx, cancel := context.WithTimeout(ctx, 3*time.Second)
		defer cancel()
		values, err := CollectQueues(sampleCtx, db, time.Now().UTC())
		if err != nil {
			if ctx.Err() == nil {
				log.Warn("observability.queues.failed", "event", "observability.queues.failed", "error", err)
			}
			return
		}
		observability.SetQueueSnapshot(values)
	}
	collect()
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			collect()
		}
	}
}
