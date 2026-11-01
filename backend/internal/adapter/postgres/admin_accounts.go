package postgres

import (
	"context"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

// The transaction-wide lock serializes role changes, including last-admin checks.
func (r *PlayerRepo) ChangeAccount(ctx context.Context, a player.AccountAudit) error {
	q := execer(ctx, r.db)
	if _, err := q.ExecContext(ctx, `SELECT pg_advisory_xact_lock(721031)`); err != nil {
		return err
	}
	actor, err := r.FindByID(ctx, a.ActorID)
	if err != nil {
		return err
	}
	if actor.Role != player.RoleAdmin || actor.Status != player.StatusActive {
		return apperror.New(apperror.Forbidden, "Требуется действующий администратор")
	}
	p, err := r.FindByID(ctx, a.PlayerID)
	if err != nil {
		return err
	}
	if p.Role == player.RoleAdmin && p.Status == player.StatusActive && (a.Role != player.RoleAdmin || a.Status != player.StatusActive) {
		var count int
		if err := q.QueryRowContext(ctx, `SELECT count(*) FROM players WHERE role='admin' AND status='active'`).Scan(&count); err != nil {
			return err
		}
		if count <= 1 {
			return apperror.New(apperror.Conflict, "Нельзя отключить последнего администратора")
		}
	}
	if _, err := q.ExecContext(ctx, `UPDATE players SET status=$2,role=$3,updated_at=$4 WHERE id=$1`, a.PlayerID, a.Status, a.Role, a.CreatedAt); err != nil {
		return err
	}
	_, err = q.ExecContext(ctx, `INSERT INTO account_admin_audit(id,actor_id,player_id,status,role,previous_status,previous_role,reason,created_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)`, a.ID, a.ActorID, a.PlayerID, a.Status, a.Role, p.Status, p.Role, a.Reason, a.CreatedAt)
	return err
}

func (r *PlayerRepo) AccountAudit(ctx context.Context, limit int) ([]player.AccountAudit, error) {
	if limit < 1 || limit > 100 {
		limit = 100
	}
	rows, err := execer(ctx, r.db).QueryContext(ctx, `SELECT id,actor_id,player_id,status,role,previous_status,previous_role,reason,created_at FROM account_admin_audit ORDER BY created_at DESC,id DESC LIMIT $1`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []player.AccountAudit{}
	for rows.Next() {
		var a player.AccountAudit
		if err := rows.Scan(&a.ID, &a.ActorID, &a.PlayerID, &a.Status, &a.Role, &a.PreviousStatus, &a.PreviousRole, &a.Reason, &a.CreatedAt); err != nil {
			return nil, err
		}
		items = append(items, a)
	}
	return items, rows.Err()
}
