package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func TestRaidStartCooldownAndResolve(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	actions := memory.NewActionRepo()
	now := time.Date(2026, 10, 25, 12, 0, 0, 0, time.UTC)
	for _, item := range []building.Building{
		{ID: "attacker", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeTownHall, State: building.StateActive, Health: 100, Tile: world.Coord{X: 4, Y: 4}},
		{ID: "defender", MapID: DefaultWorldID, OwnerID: "p2", Type: building.TypeTownHall, State: building.StateActive, Health: 100, Tile: world.Coord{X: 5, Y: 4}},
	} {
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	s := NewRaidService(buildings, actions, slog.New(slog.NewTextHandler(io.Discard, nil)))
	s.now = func() time.Time { return now }
	if _, err := s.Start(ctx, player.ID("p1"), "attacker"); err == nil {
		t.Fatal("own building accepted as target")
	}
	raid, err := s.Start(ctx, player.ID("p1"), "defender")
	if err != nil {
		t.Fatal(err)
	}
	if raid.Status != action.StatusPending || raid.DueAt != now.Add(time.Duration(catalog.RaidRules().RaidTravelSeconds)*time.Second) {
		t.Fatalf("raid=%+v", raid)
	}
	if _, err := s.Start(ctx, player.ID("p1"), "defender"); err == nil {
		t.Fatal("cooldown was bypassed")
	}
	items, err := actions.ListRaids(ctx, player.ID("p1"))
	if err != nil || len(items) != 1 {
		t.Fatalf("actions=%+v err=%v", items, err)
	}
	if err := s.Resolve(ctx, items[0], raid.DueAt); err != nil {
		t.Fatal(err)
	}
	target, err := buildings.FindByID(ctx, "defender")
	if err != nil {
		t.Fatal(err)
	}
	if target.Health != 100-catalog.RaidRules().RaidDamage || target.State != building.StateDamaged {
		t.Fatalf("target=%+v", target)
	}
	raids, err := s.List(ctx, player.ID("p1"))
	if err != nil || len(raids) != 1 || raids[0].Status != action.StatusDone {
		t.Fatalf("raids=%+v err=%v", raids, err)
	}
}

func TestRaidDestroysOilWellAndReleasesDeposit(t *testing.T) {
	ctx := context.Background()
	_, resources, buildings, nodes, _, well := oilFixture(t)
	well.State, well.Health = building.StateActive, 20
	if err := buildings.Update(ctx, well); err != nil {
		t.Fatal(err)
	}
	if err := buildings.Create(ctx, building.Building{ID: "raider", MapID: DefaultWorldID, OwnerID: "p2", Type: building.TypeTownHall,
		State: building.StateActive, Health: 100, Tile: world.Coord{X: well.Tile.X + 1, Y: well.Tile.Y}}); err != nil {
		t.Fatal(err)
	}
	actions := memory.NewActionRepo()
	raids := NewRaidService(buildings, actions, slog.New(slog.NewTextHandler(io.Discard, nil)))
	raids.SetResources(resources)
	started, err := raids.Start(ctx, player.ID("p2"), well.ID)
	if err != nil {
		t.Fatal(err)
	}
	items, err := actions.ListRaids(ctx, player.ID("p2"))
	if err != nil || len(items) != 1 {
		t.Fatalf("actions=%+v err=%v", items, err)
	}
	if err := raids.Resolve(ctx, items[0], started.DueAt); err != nil {
		t.Fatal(err)
	}
	if _, err := buildings.FindByID(ctx, well.ID); err == nil {
		t.Fatal("destroyed oil well still occupies the tile")
	}
	node, err := nodes.FindResourceNode(ctx, "node_oil_1")
	if err != nil {
		t.Fatal(err)
	}
	if node.OwnerID != "" || node.State != economy.NodeNeutral {
		t.Fatalf("deposit remains claimed: %+v", node)
	}
}
