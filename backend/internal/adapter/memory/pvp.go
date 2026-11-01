package memory

import (
	"context"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"real-city/backend/pkg/memorytx"
	"time"
)

func (r *PlayerRepo) PvPProtection(ctx context.Context, id player.ID, now time.Time, damage, health int) (player.PvPState, int, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.players[id]
	if !ok {
		return player.PvPState{}, 0, apperror.New(apperror.NotFound, "Игрок не найден")
	}
	seen := p.CreatedAt
	if presence, ok := r.presence[id]; ok {
		seen = presence.UpdatedAt
	}
	state, allowed := player.ApplyPvPDamage(r.pvp[id], seen, now, damage, health)
	if r.pvp == nil {
		r.pvp = map[player.ID]player.PvPState{}
	}
	r.pvp[id] = state
	return state, allowed, nil
}
