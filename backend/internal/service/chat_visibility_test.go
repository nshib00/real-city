package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
)

func TestNearbyChatAudienceAndPagination(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewSocialRepo()
	buildings := memory.NewBuildingRepo()
	for _, b := range []building.Building{
		{ID: "sender", OwnerID: "sender", MapID: "world", Tile: world.Coord{X: 0, Y: 0}, Health: 100, State: building.StateActive},
		{ID: "near", OwnerID: "near", MapID: "world", Tile: world.Coord{X: worldgen.WorldSizeTiles - 1, Y: 0}, Health: 100, State: building.StateActive},
		{ID: "far", OwnerID: "far", MapID: "world", Tile: world.Coord{X: 100, Y: 100}, Health: 100, State: building.StateActive},
		{ID: "other", OwnerID: "other", MapID: "other", Tile: world.Coord{X: 0, Y: 0}, Health: 100, State: building.StateActive},
	} {
		if err := buildings.Create(ctx, b); err != nil {
			t.Fatal(err)
		}
	}
	s := NewChatService(repo, repo, slog.Default())
	s.SetBuildings(buildings)
	bus := NewEventBus(32)
	s.SetEventBus(bus)
	events := bus.Subscribe(ctx)
	now := time.Now().UTC()
	s.now = func() time.Time { now = now.Add(time.Microsecond); return now }
	for i := 0; i < 3; i++ {
		if _, err := s.Send(ctx, "sender", chat.ChannelNearby, "", "Привет соседям"); err != nil {
			t.Fatal(err)
		}
	}
	for i := 0; i < 6; i++ {
		select {
		case event := <-events:
			if event.PlayerID != "sender" && event.PlayerID != "near" {
				t.Fatalf("nearby event leaked: %+v", event)
			}
		default:
			t.Fatal("missing private event")
		}
	}
	for _, id := range []player.ID{"far", "other"} {
		items, err := s.List(ctx, id, chat.ChannelNearby, 10)
		if err != nil || len(items) != 0 {
			t.Fatalf("history leaked to %s: %+v %v", id, items, err)
		}
		count, _ := repo.CountUnread(ctx, id, chat.ChannelNearby, "", time.Time{})
		if count != 0 {
			t.Fatal("unread leaked")
		}
	}
	first, err := s.List(ctx, "near", chat.ChannelNearby, 2)
	if err != nil || len(first) != 2 {
		t.Fatalf("first page: %+v %v", first, err)
	}
	last := first[len(first)-1]
	second, err := s.List(ctx, "near", chat.ChannelNearby, 2, chat.Cursor{CreatedAt: last.CreatedAt, ID: last.ID})
	if err != nil || len(second) != 1 || second[0].ID == last.ID {
		t.Fatalf("second page: %+v %v", second, err)
	}
}

func TestChatCursorHandlesEqualTimestamps(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewSocialRepo()
	at := time.Now().UTC()
	for _, id := range []chat.MessageID{"a", "c", "b"} {
		if err := repo.AddMessage(ctx, chat.Message{ID: id, AuthorID: "p", Channel: chat.ChannelGlobal, CreatedAt: at}); err != nil {
			t.Fatal(err)
		}
	}
	items, err := repo.ListMessages(ctx, "viewer", chat.ChannelGlobal, "", 2, chat.Cursor{CreatedAt: at, ID: "c"})
	if err != nil || len(items) != 2 || items[0].ID != "b" || items[1].ID != "a" {
		t.Fatalf("unstable cursor: %+v %v", items, err)
	}
}
