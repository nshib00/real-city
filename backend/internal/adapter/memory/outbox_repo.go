package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/pkg/apperror"
)

type OutboxRepo struct {
	mu     sync.RWMutex
	events map[outbox.ID]outbox.OutboxEvent
}

func NewOutboxRepo() *OutboxRepo {
	return &OutboxRepo{events: make(map[outbox.ID]outbox.OutboxEvent)}
}

func (r *OutboxRepo) Append(ctx context.Context, item outbox.OutboxEvent) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.events[item.ID]; ok {
		return nil
	}
	r.events[item.ID] = item
	return nil
}

func (r *OutboxRepo) FetchDue(ctx context.Context, now time.Time, limit int, lockTTL time.Duration) ([]outbox.OutboxEvent, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	items := make([]outbox.OutboxEvent, 0)
	for _, item := range r.events {
		locked := item.LockedUntil != nil && item.LockedUntil.After(now)
		if item.Status == outbox.StatusPending && !item.NextAttemptAt.After(now) && !locked {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].NextAttemptAt.Before(items[j].NextAttemptAt) })
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	lockedUntil := now.Add(lockTTL)
	for index, item := range items {
		item.LockedUntil = &lockedUntil
		item.UpdatedAt = now
		r.events[item.ID] = item
		items[index] = item
	}
	return items, nil
}

func (r *OutboxRepo) MarkSent(ctx context.Context, id outbox.ID, now time.Time) error {
	_ = ctx
	return r.update(id, func(item *outbox.OutboxEvent) {
		item.Status = outbox.StatusSent
		item.LockedUntil = nil
		item.UpdatedAt = now
	})
}

func (r *OutboxRepo) MarkFailed(ctx context.Context, id outbox.ID, message string, retryAt time.Time, now time.Time) error {
	_ = ctx
	return r.update(id, func(item *outbox.OutboxEvent) {
		item.Status = outbox.StatusPending
		item.Attempts++
		item.LastError = message
		item.NextAttemptAt = retryAt
		item.LockedUntil = nil
		item.UpdatedAt = now
	})
}

func (r *OutboxRepo) MarkDead(ctx context.Context, id outbox.ID, message string, now time.Time) error {
	_ = ctx
	return r.update(id, func(item *outbox.OutboxEvent) {
		item.Status = outbox.StatusDead
		item.Attempts++
		item.LastError = message
		item.LockedUntil = nil
		item.UpdatedAt = now
	})
}

func (r *OutboxRepo) PruneSent(ctx context.Context, before time.Time, limit int) (int, error) {
	_ = ctx
	if limit <= 0 {
		return 0, nil
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	pruned := 0
	for id, item := range r.events {
		if item.Status == outbox.StatusSent && item.UpdatedAt.Before(before) {
			delete(r.events, id)
			pruned++
			if pruned == limit {
				break
			}
		}
	}
	return pruned, nil
}

func (r *OutboxRepo) update(id outbox.ID, fn func(*outbox.OutboxEvent)) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	item, ok := r.events[id]
	if !ok {
		return apperror.New(apperror.NotFound, "outbox event not found")
	}
	fn(&item)
	r.events[id] = item
	return nil
}
