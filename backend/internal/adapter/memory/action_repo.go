package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ActionRepo struct {
	mu      sync.RWMutex
	actions map[action.ID]action.GameAction
	keys    map[string]action.ID
}

func NewActionRepo() *ActionRepo {
	return &ActionRepo{actions: make(map[action.ID]action.GameAction), keys: make(map[string]action.ID)}
}

func (r *ActionRepo) Append(ctx context.Context, item action.GameAction) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if item.IdempotencyKey != "" {
		if _, ok := r.keys[item.IdempotencyKey]; ok {
			return nil
		}
		r.keys[item.IdempotencyKey] = item.ID
	}
	r.actions[item.ID] = item
	return nil
}

func (r *ActionRepo) AppendUnique(ctx context.Context, item action.GameAction) (bool, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, exists := r.keys[item.IdempotencyKey]; exists {
		return false, nil
	}
	r.keys[item.IdempotencyKey] = item.ID
	r.actions[item.ID] = item
	return true, nil
}

func (r *ActionRepo) HasIdempotencyKey(ctx context.Context, key string) (bool, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	_, exists := r.keys[key]
	return exists, nil
}

func (r *ActionRepo) ListPendingWeapons(ctx context.Context, playerID player.ID) ([]action.GameAction, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]action.GameAction, 0)
	for _, item := range r.actions {
		if item.Actor.ID == string(playerID) && item.Type == action.TypeDetonateWeapon && (item.Status == action.StatusPending || item.Status == action.StatusRunning) {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].DueAt.Before(items[j].DueAt) })
	return items, nil
}

func (r *ActionRepo) ListRaids(ctx context.Context, playerID player.ID) ([]action.GameAction, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]action.GameAction, 0)
	for _, item := range r.actions {
		if item.Actor.ID == string(playerID) && item.Type == action.TypeResolveRaid {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.After(items[j].CreatedAt) })
	if len(items) > 200 {
		items = items[:200]
	}
	return items, nil
}

func (r *ActionRepo) HasRecentRaid(ctx context.Context, playerID player.ID, targetID building.ID, since time.Time) (bool, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, item := range r.actions {
		if item.Type == action.TypeResolveRaid && item.Actor.ID == string(playerID) && item.Target.ID == string(targetID) && !item.CreatedAt.Before(since) {
			return true, nil
		}
	}
	return false, nil
}

func (r *ActionRepo) FetchDue(ctx context.Context, now time.Time, limit int, lockTTL time.Duration) ([]action.GameAction, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	items := make([]action.GameAction, 0)
	for _, item := range r.actions {
		locked := item.LockedUntil != nil && item.LockedUntil.After(now)
		if (item.Status == action.StatusPending || item.Status == action.StatusRunning) && !item.DueAt.After(now) && !locked {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].DueAt.Before(items[j].DueAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	lockedUntil := now.Add(lockTTL)
	for index, item := range items {
		item.Status = action.StatusRunning
		item.LockedUntil = &lockedUntil
		item.UpdatedAt = now
		r.actions[item.ID] = item
		items[index] = item
	}
	return items, nil
}

func (r *ActionRepo) MarkDone(ctx context.Context, id action.ID, now time.Time) error {
	_ = ctx
	return r.update(id, func(item *action.GameAction) {
		item.Status = action.StatusDone
		item.LockedUntil = nil
		item.UpdatedAt = now
	})
}

func (r *ActionRepo) MarkFailed(ctx context.Context, id action.ID, message string, retryAt time.Time, now time.Time) error {
	_ = ctx
	return r.update(id, func(item *action.GameAction) {
		item.Status = action.StatusPending
		item.Attempts++
		item.LastError = message
		item.DueAt = retryAt
		item.LockedUntil = nil
		item.UpdatedAt = now
	})
}

func (r *ActionRepo) update(id action.ID, fn func(*action.GameAction)) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	item, ok := r.actions[id]
	if !ok {
		return apperror.New(apperror.NotFound, "action not found")
	}
	fn(&item)
	r.actions[id] = item
	return nil
}
