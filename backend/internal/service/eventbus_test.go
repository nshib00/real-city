package service

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestEventBusPublishesToSubscribers(t *testing.T) {
	bus := NewEventBus(2)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	events := bus.Subscribe(ctx)

	bus.Publish(Event{Type: EventTileChanged, ChunkID: "dev-world:0:0"})

	select {
	case event := <-events:
		if event.Type != EventTileChanged || event.ChunkID != "dev-world:0:0" || event.CreatedAt.IsZero() {
			t.Fatalf("unexpected event: %#v", event)
		}
	case <-time.After(time.Second):
		t.Fatal("expected event")
	}
}

func TestEventBusDoesNotDeliverLocallyWhenForwardingFails(t *testing.T) {
	bus := NewEventBus(2)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	events := bus.Subscribe(ctx)
	want := errors.New("outbox unavailable")
	bus.SetForwarder(func(Event) error { return want })
	if err := bus.Publish(Event{Type: EventTileChanged}); !errors.Is(err, want) {
		t.Fatalf("expected forwarding error, got %v", err)
	}
	select {
	case event := <-events:
		t.Fatalf("event should not be delivered after failed forwarding: %#v", event)
	default:
	}
}

func TestEventBusSignalsDroppedEvents(t *testing.T) {
	bus := NewEventBus(1)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	_ = bus.Subscribe(ctx)
	dropped := 0
	bus.SetDropHandler(func(Event) { dropped++ })
	_ = bus.Publish(Event{Type: EventTileChanged})
	_ = bus.Publish(Event{Type: EventTileChanged})
	if dropped != 1 {
		t.Fatalf("drop notifications = %d, want 1", dropped)
	}
}
