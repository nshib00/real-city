package memory

import (
	"context"
	"encoding/json"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"real-city/backend/pkg/memorytx"
)

type ActionRepo struct {
	mu      sync.RWMutex
	actions map[action.ID]action.GameAction
	keys    map[string]action.ID
}

func NewActionRepo() *ActionRepo {
	return &ActionRepo{actions: make(map[action.ID]action.GameAction), keys: make(map[string]action.ID)}
}

func (r *ActionRepo) ListCombatRecords(ctx context.Context, id player.ID, limit int) ([]action.GameAction, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := []action.GameAction{}
	for _, item := range r.actions {
		if item.Type != "combat_record" {
			continue
		}
		var payload struct {
			OwnerID string `json:"owner_id"`
		}
		if err := json.Unmarshal(item.Payload, &payload); err != nil {
			return nil, err
		}
		if item.Actor.ID == string(id) || payload.OwnerID == string(id) {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].CreatedAt.Equal(items[j].CreatedAt) {
			return items[i].ID > items[j].ID
		}
		return items[i].CreatedAt.After(items[j].CreatedAt)
	})
	if limit < 1 || limit > 100 {
		limit = 50
	}
	if len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (r *ActionRepo) Append(ctx context.Context, item action.GameAction) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	_, exists := r.keys[key]
	return exists, nil
}

func (r *ActionRepo) ListPendingWeapons(ctx context.Context, playerID player.ID) ([]action.GameAction, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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

func (r *ActionRepo) FetchDue(ctx context.Context, now time.Time, limit int, lockTTL time.Duration) ([]action.GameAction, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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

func (r *ActionRepo) LockCombatActor(context.Context, player.ID) error { return nil }

func (r *ActionRepo) HasRecentAction(ctx context.Context, actor player.ID, kind action.Type, since time.Time) (bool, error) {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, item := range r.actions {
		if item.Actor.ID == string(actor) && item.Type == kind && item.CreatedAt.After(since) {
			return true, nil
		}
	}
	return false, nil
}

func (r *ActionRepo) MarkDone(ctx context.Context, id action.ID, now time.Time) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
	_ = ctx
	return r.update(id, func(item *action.GameAction) {
		item.Status = action.StatusDone
		item.LockedUntil = nil
		item.UpdatedAt = now
	})
}

func (r *ActionRepo) MarkFailed(ctx context.Context, id action.ID, message string, retryAt time.Time, now time.Time) error {
	ctx, releaseGate := memorytx.Guard(ctx)
	defer releaseGate()
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
