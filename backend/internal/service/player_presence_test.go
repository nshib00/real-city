package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
)

func TestNearbyPresenceShowsOnlyActiveNearbyPlayers(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewPlayerRepo()
	for _, item := range []struct {
		id, name string
		level    int
	}{
		{"viewer", "Зритель", 1},
		{"neighbor", "Аэрон", 4},
		{"far", "Далёкий", 1},
		{"stale", "Старый", 1},
	} {
		profile := player.DefaultProfile(item.name, time.Now())
		profile.CityName = "Не никнейм"
		profile.Level = item.level
		if err := repo.Create(ctx, player.Player{ID: player.ID(item.id), Email: item.id + "@test.local", Name: item.name, Status: player.StatusActive, Profile: profile}); err != nil {
			t.Fatal(err)
		}
	}
	service := NewPlayerService(repo, memory.NewSessionStore(), slog.Default())
	for _, item := range []struct {
		id   player.ID
		x, y int
	}{
		{"viewer", 159, 10},
		{"neighbor", 0, 11},
		{"far", 70, 70},
	} {
		if err := service.UpdatePresence(ctx, item.id, item.x, item.y); err != nil {
			t.Fatal(err)
		}
	}
	if err := repo.SavePresence(ctx, "stale", 0, 10, time.Now().Add(-time.Minute)); err != nil {
		t.Fatal(err)
	}
	items, err := service.NearbyPresence(ctx, "viewer", 159, 10, 2)
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 1 || items[0].PlayerID != "neighbor" || items[0].Name != "Аэрон" || items[0].Level != 4 {
		t.Fatalf("unexpected nearby players: %+v", items)
	}
	if err := service.UpdatePresence(ctx, "viewer", 160, 10); err == nil {
		t.Fatal("out-of-bounds presence was accepted")
	}
}

func TestUpdatePresencePublishesMovementInCurrentChunk(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewPlayerRepo()
	profile := player.DefaultProfile("Аэрон", time.Now())
	profile.Level = 4
	if err := repo.Create(ctx, player.Player{ID: "neighbor", Email: "neighbor@test.local", Name: "Аэрон", Status: player.StatusActive, Profile: profile}); err != nil {
		t.Fatal(err)
	}
	bus := NewEventBus(2)
	events := bus.Subscribe(ctx)
	service := NewPlayerService(repo, memory.NewSessionStore(), slog.Default())
	service.SetEventBus(bus)
	if err := service.UpdatePresence(ctx, "neighbor", 33, 2); err != nil {
		t.Fatal(err)
	}
	select {
	case event := <-events:
		movement, ok := event.Payload.(PresenceMovedPayload)
		if !ok || event.Type != EventPresenceMoved || event.ChunkID != "dev-world:1:0" || movement.Player.PlayerID != "neighbor" || movement.Player.Name != "Аэрон" || movement.Player.Level != 4 || movement.Player.TileX != 33 {
			t.Fatalf("unexpected movement event: %+v", event)
		}
	case <-time.After(time.Second):
		t.Fatal("movement event was not published")
	}
}
