package service

import (
	"context"
	"log/slog"
	"sync"
	"time"
)

type EventBus struct {
	mu          sync.RWMutex
	subscribers map[uint64]chan Event
	nextID      uint64
	buffer      int
	logDropped  func(Event)
	forward     func(Event) error
}

// SetForwarder sends published events to a shared transport before local delivery.
// It is used by the standalone simulation worker; API buses have no forwarder.
func (b *EventBus) SetForwarder(forward func(Event) error) {
	b.mu.Lock()
	b.forward = forward
	b.mu.Unlock()
}

func (b *EventBus) SetDropHandler(handler func(Event)) {
	b.mu.Lock()
	b.logDropped = handler
	b.mu.Unlock()
}

func NewEventBus(buffer int) *EventBus {
	if buffer <= 0 {
		buffer = 64
	}
	return &EventBus{subscribers: make(map[uint64]chan Event), buffer: buffer}
}

func (b *EventBus) Subscribe(ctx context.Context) <-chan Event {
	ch := make(chan Event, b.buffer)
	b.mu.Lock()
	b.nextID++
	id := b.nextID
	b.subscribers[id] = ch
	b.mu.Unlock()
	go func() {
		<-ctx.Done()
		b.mu.Lock()
		delete(b.subscribers, id)
		close(ch)
		b.mu.Unlock()
	}()
	return ch
}

func (b *EventBus) Publish(event Event) error {
	if event.CreatedAt.IsZero() {
		event.CreatedAt = time.Now().UTC()
	}
	b.mu.RLock()
	forward := b.forward
	b.mu.RUnlock()
	if forward != nil {
		if err := forward(event); err != nil {
			slog.Error("event.forward.failed", "event", "event.forward.failed", "event_type", event.Type, "error", err)
			return err
		}
	}
	b.mu.RLock()
	defer b.mu.RUnlock()
	for _, ch := range b.subscribers {
		select {
		case ch <- event:
		default:
			if b.logDropped != nil {
				b.logDropped(event)
			}
		}
	}
	return nil
}
