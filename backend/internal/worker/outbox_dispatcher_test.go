package worker

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

func TestOutboxDispatcherPublishesEvent(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewOutboxRepo()
	bus := service.NewEventBus(2)
	events := bus.Subscribe(ctx)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	item := outbox.NewOutboxEvent("evt1", string(service.EventTileChanged), "tile:1:2", []byte(`{"ok":true}`), now)
	item.ChunkID = "dev-world:0:0"
	item.PlayerID = "p1"
	if err := repo.Append(ctx, item); err != nil {
		t.Fatalf("append outbox: %v", err)
	}

	dispatcher := NewOutboxDispatcher(repo, bus, slog.New(slog.NewTextHandler(io.Discard, nil)), config.SimulationConfig{BatchSize: 10, TickInterval: time.Second, LockTTL: time.Second})
	dispatcher.now = func() time.Time { return now }
	if _, err := dispatcher.Dispatch(ctx); err != nil {
		t.Fatalf("dispatch: %v", err)
	}

	select {
	case event := <-events:
		if event.Type != service.EventTileChanged || event.ChunkID != "dev-world:0:0" {
			t.Fatalf("unexpected event: %#v", event)
		}
	case <-time.After(time.Second):
		t.Fatal("expected event")
	}
}
