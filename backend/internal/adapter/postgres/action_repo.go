package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ActionRepo struct {
	db *sql.DB
}

func (r *ActionRepo) LockCombatActor(ctx context.Context, actor player.ID) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `SELECT pg_advisory_xact_lock(hashtextextended($1, 0))`, "combat:"+string(actor))
	return err
}

func (r *ActionRepo) HasRecentAction(ctx context.Context, actor player.ID, kind action.Type, since time.Time) (bool, error) {
	var found bool
	err := execer(ctx, r.db).QueryRowContext(ctx, `SELECT EXISTS(SELECT 1 FROM game_actions WHERE actor_id=$1 AND type=$2 AND created_at > $3)`, actor, kind, since).Scan(&found)
	return found, err
}

func NewActionRepo(db *sql.DB) *ActionRepo {
	return &ActionRepo{db: db}
}

func (r *ActionRepo) ListCombatRecords(ctx context.Context, id player.ID, limit int) ([]action.GameAction, error) {
	if limit < 1 || limit > 100 {
		limit = 50
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,type,status,idempotency_key,actor_id,actor_type,target_id,target_type,payload,due_at,locked_until,attempts,last_error,created_at,updated_at FROM game_actions WHERE type='combat_record' AND (actor_id=$1 OR payload->>'owner_id'=$1) ORDER BY created_at DESC,id DESC LIMIT $2`, id, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []action.GameAction{}
	for rows.Next() {
		item, err := scanAction(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *ActionRepo) Append(ctx context.Context, item action.GameAction) error {
	_, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO game_actions (
			id, type, status, idempotency_key, actor_id, actor_type, target_id, target_type,
			payload, due_at, locked_until, attempts, last_error, created_at, updated_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
		ON CONFLICT (idempotency_key) DO NOTHING
	`, item.ID, item.Type, item.Status, item.IdempotencyKey, item.Actor.ID, item.Actor.Type, item.Target.ID, item.Target.Type, item.Payload, item.DueAt, item.LockedUntil, item.Attempts, item.LastError, item.CreatedAt, item.UpdatedAt)
	return err
}

func (r *ActionRepo) AppendUnique(ctx context.Context, item action.GameAction) (bool, error) {
	result, err := execer(ctx, r.db).ExecContext(ctx, `
		INSERT INTO game_actions (id, type, status, idempotency_key, actor_id, actor_type, target_id, target_type,
			payload, due_at, locked_until, attempts, last_error, created_at, updated_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
		ON CONFLICT (idempotency_key) DO NOTHING
	`, item.ID, item.Type, item.Status, item.IdempotencyKey, item.Actor.ID, item.Actor.Type, item.Target.ID, item.Target.Type, item.Payload, item.DueAt, item.LockedUntil, item.Attempts, item.LastError, item.CreatedAt, item.UpdatedAt)
	if err != nil {
		return false, err
	}
	affected, err := result.RowsAffected()
	return affected == 1, err
}

func (r *ActionRepo) HasIdempotencyKey(ctx context.Context, key string) (bool, error) {
	var exists bool
	err := execer(ctx, r.db).QueryRowContext(ctx, `SELECT EXISTS (SELECT 1 FROM game_actions WHERE idempotency_key = $1)`, key).Scan(&exists)
	return exists, err
}

func (r *ActionRepo) ListPendingWeapons(ctx context.Context, playerID player.ID) ([]action.GameAction, error) {
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		SELECT id, type, status, idempotency_key, actor_id, actor_type, target_id, target_type,
			payload, due_at, locked_until, attempts, last_error, created_at, updated_at
		FROM game_actions
		WHERE actor_id = $1 AND type = $2 AND status IN ('pending', 'running')
		ORDER BY due_at, id LIMIT 200
	`, playerID, action.TypeDetonateWeapon)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]action.GameAction, 0)
	for rows.Next() {
		item, err := scanAction(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *ActionRepo) FetchDue(ctx context.Context, now time.Time, limit int, lockTTL time.Duration) (items []action.GameAction, resultErr error) {
	defer observe("action.fetch_due", time.Now(), &resultErr)
	if limit <= 0 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `
		WITH due AS (
			SELECT id
			FROM game_actions
			WHERE (status = $1 OR (status = 'running' AND locked_until <= $2))
			  AND due_at <= $2
			  AND (locked_until IS NULL OR locked_until <= $2)
			ORDER BY due_at, id
			LIMIT $3
			FOR UPDATE SKIP LOCKED
		)
		UPDATE game_actions
		SET status = $4, locked_until = $5, updated_at = $2
		WHERE id IN (SELECT id FROM due)
		RETURNING id, type, status, idempotency_key, actor_id, actor_type, target_id, target_type,
			payload, due_at, locked_until, attempts, last_error, created_at, updated_at
	`, action.StatusPending, now, limit, action.StatusRunning, now.Add(lockTTL))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items = make([]action.GameAction, 0)
	for rows.Next() {
		item, err := scanAction(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *ActionRepo) MarkDone(ctx context.Context, id action.ID, now time.Time) (resultErr error) {
	defer observe("action.mark_done", time.Now(), &resultErr)
	return r.update(ctx, id, `
		UPDATE game_actions
		SET status = $2, locked_until = NULL, updated_at = $3
		WHERE id = $1
	`, action.StatusDone, now)
}

func (r *ActionRepo) MarkFailed(ctx context.Context, id action.ID, message string, retryAt time.Time, now time.Time) (resultErr error) {
	defer observe("action.mark_failed", time.Now(), &resultErr)
	return r.update(ctx, id, `
		UPDATE game_actions
		SET status = $2, attempts = attempts + 1, last_error = $3, due_at = $4, locked_until = NULL, updated_at = $5
		WHERE id = $1
	`, action.StatusPending, message, retryAt, now)
}

func (r *ActionRepo) update(ctx context.Context, id action.ID, query string, args ...any) error {
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
		return apperror.New(apperror.NotFound, "action not found")
	}
	return nil
}

func scanAction(row interface{ Scan(dest ...any) error }) (action.GameAction, error) {
	var item action.GameAction
	var actorID, actorType, targetID, targetType string
	err := row.Scan(&item.ID, &item.Type, &item.Status, &item.IdempotencyKey, &actorID, &actorType, &targetID, &targetType, &item.Payload, &item.DueAt, &item.LockedUntil, &item.Attempts, &item.LastError, &item.CreatedAt, &item.UpdatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return action.GameAction{}, apperror.New(apperror.NotFound, "action not found")
	}
	item.Actor = action.ObjectRef{ID: actorID, Type: actorType}
	item.Target = action.ObjectRef{ID: targetID, Type: targetType}
	return item, err
}
