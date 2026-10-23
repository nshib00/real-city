package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/pkg/apperror"
)

type OutboxRepo struct {
	db *sql.DB
}

func NewOutboxRepo(db *sql.DB) *OutboxRepo {
	return &OutboxRepo{db: db}
}

func (r *OutboxRepo) Append(ctx context.Context, item outbox.OutboxEvent) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO outbox_events (
			id, type, aggregate_id, chunk_id, player_id, alliance, payload,
			status, attempts, next_attempt_at, locked_until, last_error, created_at, updated_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
		ON CONFLICT (id) DO NOTHING
	`, item.ID, item.Type, item.AggregateID, item.ChunkID, item.PlayerID, item.Alliance, item.Payload, item.Status, item.Attempts, item.NextAttemptAt, item.LockedUntil, item.LastError, item.CreatedAt, item.UpdatedAt)
	return err
}

func (r *OutboxRepo) FetchDue(ctx context.Context, now time.Time, limit int, lockTTL time.Duration) (items []outbox.OutboxEvent, resultErr error) {
	defer observe("outbox.fetch_due", time.Now(), &resultErr)
	_ = lockTTL
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		WITH due AS (
			SELECT id
			FROM outbox_events
			WHERE status = $1
			  AND next_attempt_at <= $2
			  AND (locked_until IS NULL OR locked_until <= $2)
			ORDER BY next_attempt_at, id
			LIMIT $3
			FOR UPDATE SKIP LOCKED
		)
		UPDATE outbox_events
		SET locked_until = $4, updated_at = $2
		WHERE id IN (SELECT id FROM due)
		RETURNING id, type, aggregate_id, chunk_id, player_id, alliance, payload,
			status, attempts, next_attempt_at, locked_until, last_error, created_at, updated_at
	`, outbox.StatusPending, now, limit, now.Add(lockTTL))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items = make([]outbox.OutboxEvent, 0)
	for rows.Next() {
		item, err := scanOutboxEvent(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *OutboxRepo) MarkSent(ctx context.Context, id outbox.ID, now time.Time) (resultErr error) {
	defer observe("outbox.mark_sent", time.Now(), &resultErr)
	return r.update(ctx, id, `
		UPDATE outbox_events SET status = $2, locked_until = NULL, updated_at = $3 WHERE id = $1
	`, outbox.StatusSent, now)
}

func (r *OutboxRepo) MarkFailed(ctx context.Context, id outbox.ID, message string, retryAt time.Time, now time.Time) (resultErr error) {
	defer observe("outbox.mark_failed", time.Now(), &resultErr)
	return r.update(ctx, id, `
		UPDATE outbox_events
		SET status = $2, attempts = attempts + 1, last_error = $3, next_attempt_at = $4, locked_until = NULL, updated_at = $5
		WHERE id = $1
	`, outbox.StatusPending, message, retryAt, now)
}

func (r *OutboxRepo) MarkDead(ctx context.Context, id outbox.ID, message string, now time.Time) (resultErr error) {
	defer observe("outbox.mark_dead", time.Now(), &resultErr)
	return r.update(ctx, id, `
		UPDATE outbox_events
		SET status = $2, attempts = attempts + 1, last_error = $3, locked_until = NULL, updated_at = $4
		WHERE id = $1
	`, outbox.StatusDead, message, now)
}

func (r *OutboxRepo) update(ctx context.Context, id outbox.ID, query string, args ...any) error {
	params := append([]any{id}, args...)
	result, err := execer(ctx, r.db).ExecContext(ctx, query, params...)
	if err != nil {
		return err
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if affected == 0 {
		return apperror.New(apperror.NotFound, "outbox event not found")
	}
	return nil
}

func scanOutboxEvent(row interface{ Scan(dest ...any) error }) (outbox.OutboxEvent, error) {
	var item outbox.OutboxEvent
	err := row.Scan(&item.ID, &item.Type, &item.AggregateID, &item.ChunkID, &item.PlayerID, &item.Alliance, &item.Payload, &item.Status, &item.Attempts, &item.NextAttemptAt, &item.LockedUntil, &item.LastError, &item.CreatedAt, &item.UpdatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return outbox.OutboxEvent{}, apperror.New(apperror.NotFound, "outbox event not found")
	}
	return item, err
}
