package service

import (
	"context"

	"real-city/backend/pkg/memorytx"
)

type pendingEventsKey struct{}
type pendingEvent struct {
	bus   *EventBus
	event Event
}

// Events become visible only after the transaction commits.
func transactional(ctx context.Context, uow UnitOfWork, fn func(context.Context) error) error {
	if ctx.Value(pendingEventsKey{}) != nil {
		return fn(ctx)
	}
	pending := []pendingEvent{}
	ctx = context.WithValue(ctx, pendingEventsKey{}, &pending)
	var err error
	if uow == nil {
		err = fn(ctx)
	} else {
		err = uow.Do(ctx, fn)
	}
	if err != nil {
		return err
	}
	for _, item := range pending {
		_ = item.bus.Publish(item.event)
	}
	return nil
}
func publishEvent(ctx context.Context, bus *EventBus, event Event) {
	if bus == nil {
		return
	}
	if pending, ok := ctx.Value(pendingEventsKey{}).(*[]pendingEvent); ok {
		*pending = append(*pending, pendingEvent{bus, event})
		return
	}
	_ = bus.Publish(event)
}

type snapshotter interface{ Snapshot() func() }
type snapshotUnitOfWork struct{ repositories []any }

func (u snapshotUnitOfWork) Do(ctx context.Context, fn func(context.Context) error) error {
	ctx, releaseGate := memorytx.Begin(ctx)
	defer releaseGate()
	undo := []func(){}
	for _, r := range u.repositories {
		if repo, ok := r.(snapshotter); ok {
			undo = append(undo, repo.Snapshot())
		}
	}
	success := false
	defer func() {
		if !success {
			for i := len(undo) - 1; i >= 0; i-- {
				undo[i]()
			}
		}
	}()
	if err := fn(ctx); err != nil {
		return err
	}
	success = true
	return nil
}
