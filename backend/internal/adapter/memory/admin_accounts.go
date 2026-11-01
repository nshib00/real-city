package memory

import (
	"context"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"real-city/backend/pkg/memorytx"
)

func (r *PlayerRepo) ChangeAccount(ctx context.Context, a player.AccountAudit) error {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.Lock()
	defer r.mu.Unlock()
	actor := r.players[a.ActorID]
	if actor.Role != player.RoleAdmin || actor.Status != player.StatusActive {
		return apperror.New(apperror.Forbidden, "Требуется действующий администратор")
	}
	p, ok := r.players[a.PlayerID]
	if !ok || p.Status == player.StatusDeleted {
		return apperror.New(apperror.NotFound, "Игрок не найден")
	}
	if p.Role == player.RoleAdmin && p.Status == player.StatusActive && (a.Role != player.RoleAdmin || a.Status != player.StatusActive) {
		count := 0
		for _, item := range r.players {
			if item.Role == player.RoleAdmin && item.Status == player.StatusActive {
				count++
			}
		}
		if count <= 1 {
			return apperror.New(apperror.Conflict, "Нельзя отключить последнего администратора")
		}
	}
	a.PreviousRole, a.PreviousStatus = p.Role, p.Status
	p.Status, p.Role, p.UpdatedAt = a.Status, a.Role, a.CreatedAt
	r.players[p.ID] = p
	r.accountAudit = append(r.accountAudit, a)
	return nil
}

func (r *PlayerRepo) AccountAudit(ctx context.Context, limit int) ([]player.AccountAudit, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.RLock()
	defer r.mu.RUnlock()
	if limit < 1 || limit > 100 {
		limit = 100
	}
	items := []player.AccountAudit{}
	for i := len(r.accountAudit) - 1; i >= 0 && len(items) < limit; i-- {
		items = append(items, r.accountAudit[i])
	}
	return items, nil
}
