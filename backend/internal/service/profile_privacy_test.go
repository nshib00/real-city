package service

import (
	"context"
	"encoding/json"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"testing"
	"time"
)

func TestPublicProfileDoesNotExposePrivateData(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewPlayerRepo()
	now := time.Now().UTC()
	p := player.Player{ID: "p1", Email: "private@example.invalid", Name: "Player", Status: player.StatusActive, Profile: player.DefaultProfile("Player", now), CreatedAt: now, UpdatedAt: now}
	p.Profile.AvatarID = "copper"
	p.Profile.BannerID = "forest"
	p.Profile.Title = "Строитель"
	p.Profile.HomeCenterID = "home"
	if err := repo.Create(ctx, p); err != nil {
		t.Fatal(err)
	}
	buildings := memory.NewBuildingRepo()
	if err := buildings.Create(ctx, building.Building{ID: "home", OwnerID: "p1", Type: building.TypeTownHall, State: building.StateActive, Level: 1, Tile: world.Coord{X: 159, Y: 1}}); err != nil {
		t.Fatal(err)
	}
	svc := NewPlayerService(repo, nil, slog.Default())
	svc.SetProfileSources(buildings, memory.NewSocialRepo())
	view, err := svc.PublicProfile(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	raw, _ := json.Marshal(view)
	var values map[string]any
	json.Unmarshal(raw, &values)
	for _, key := range []string{"email", "xp", "settings", "home_center_id", "avatar_url", "tile_x", "tile_y", "scores"} {
		if _, ok := values[key]; ok {
			t.Fatalf("leaked %s", key)
		}
	}
	if view.SettlementRegion == nil || view.SettlementRegion.DistrictX != 4 || view.Title != "Строитель" {
		t.Fatal(view)
	}
}
