package service

import (
	"context"
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
