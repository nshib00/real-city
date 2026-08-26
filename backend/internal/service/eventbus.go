package service

import (
	"context"
	"sync"
	"time"
)

type EventBus struct {
	mu          sync.RWMutex
	subscribers map[uint64]chan Event
	nextID      uint64
	buffer      int
	logDropped  func(Event)
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

func (b *EventBus) Publish(event Event) {
	if event.CreatedAt.IsZero() {
		event.CreatedAt = time.Now().UTC()
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
}
