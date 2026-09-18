package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func TestBuildingServiceRequiresTownHallBeforeOtherBuildings(t *testing.T) {
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	_, err := service.Place(context.Background(), PlaceBuildingInput{
		PlayerID: player.ID("p1"),
		Type:     building.TypeDugout,
		Tile:     world.Coord{X: 4, Y: 4},
	})
	if err == nil {
		t.Fatal("expected town hall requirement error")
	}
}

func TestBuildingServicePlacesTownHallAndCompletesConstruction(t *testing.T) {
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }

	townHall, err := service.Place(context.Background(), PlaceBuildingInput{
		PlayerID: player.ID("p1"),
		Type:     building.TypeTownHall,
		Tile:     world.Coord{X: 0, Y: 0},
	})
	if err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	if townHall.State != building.StateActive || townHall.CompletesAt != nil {
		t.Fatalf("town hall should be active immediately: %#v", townHall)
	}

	dugout, err := service.Place(context.Background(), PlaceBuildingInput{
		PlayerID: player.ID("p1"),
		Type:     building.TypeDugout,
		Tile:     world.Coord{X: 4, Y: 4},
	})
	if err != nil {
		t.Fatalf("place dugout: %v", err)
	}
	if dugout.State != building.StateBuilding || dugout.CompletesAt == nil {
		t.Fatalf("dugout should start under construction: %#v", dugout)
	}
	service.now = func() time.Time { return dugout.CompletesAt.Add(time.Second) }
	completed, err := service.Complete(context.Background(), dugout.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("complete dugout: %v", err)
	}
	if completed.State != building.StateActive || completed.CompletesAt != nil {
		t.Fatalf("dugout should become active: %#v", completed)
	}
}

func TestBuildingServiceUpgradesTownHallAndDugout(t *testing.T) {
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	actionRepo := memory.NewActionRepo()
	service.SetActionQueue(actionRepo)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }

	townHall, err := service.Place(context.Background(), PlaceBuildingInput{
		PlayerID: player.ID("p1"),
		Type:     building.TypeTownHall,
		Tile:     world.Coord{X: 0, Y: 0},
	})
	if err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	upgradedTownHall, err := service.Upgrade(context.Background(), townHall.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("upgrade town hall: %v", err)
	}
	if upgradedTownHall.Type != building.TypeTownHall || upgradedTownHall.Level != 2 || upgradedTownHall.State != building.StateBuilding || upgradedTownHall.CompletesAt == nil {
		t.Fatalf("town hall should start level 2 upgrade construction: %#v", upgradedTownHall)
	}
	actions, err := actionRepo.FetchDue(context.Background(), upgradedTownHall.CompletesAt.Add(time.Second), 10, time.Second)
	if err != nil {
		t.Fatalf("fetch scheduled upgrade action: %v", err)
	}
	if len(actions) != 1 || actions[0].Target.ID != string(townHall.ID) {
		t.Fatalf("town hall upgrade should schedule one completion action, got %#v", actions)
	}

	service.now = func() time.Time { return upgradedTownHall.CompletesAt.Add(time.Second) }
	completedTownHall, err := service.Complete(context.Background(), townHall.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("complete town hall upgrade: %v", err)
	}
	if completedTownHall.Level != 2 || completedTownHall.State != building.StateActive || completedTownHall.CompletesAt != nil {
		t.Fatalf("town hall should complete level 2 upgrade: %#v", completedTownHall)
	}

	service.now = func() time.Time { return now }
	dugout, err := service.Place(context.Background(), PlaceBuildingInput{
		PlayerID: player.ID("p1"),
		Type:     building.TypeDugout,
		Tile:     world.Coord{X: 4, Y: 4},
	})
	if err != nil {
		t.Fatalf("place dugout: %v", err)
	}
	service.now = func() time.Time { return dugout.CompletesAt.Add(time.Second) }
	dugout, err = service.Complete(context.Background(), dugout.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("complete dugout: %v", err)
	}
	service.now = func() time.Time { return now }
	upgradedDugout, err := service.Upgrade(context.Background(), dugout.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("upgrade dugout: %v", err)
	}
	if upgradedDugout.Type != building.TypeDugout || upgradedDugout.Level != 2 || upgradedDugout.State != building.StateBuilding || upgradedDugout.CompletesAt == nil {
		t.Fatalf("dugout should start level 2 upgrade construction: %#v", upgradedDugout)
	}
}

func TestTownHallCatalogUsesDocumentedUpgradeBalance(t *testing.T) {
	spec, ok := catalog.GetBuilding(building.TypeTownHall)
	if !ok {
		t.Fatal("town hall catalog entry not found")
	}
	if len(spec.UpgradeLevels) != 10 {
		t.Fatalf("expected 10 town hall levels, got %d", len(spec.UpgradeLevels))
	}

	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 10 || final.Health != 3530 || final.BuildDuration != 7*time.Hour+36*time.Minute {
		t.Fatalf("unexpected final town hall level: %#v", final)
	}
	if got := (building.BuildRules{BaseLimit: 8}).LimitForTownHallLevel(10); got != 35 {
		t.Fatalf("expected level 10 town hall limit 35, got %d", got)
	}
}

func TestWindleafBedCatalogUsesDocumentedUpgradeBalance(t *testing.T) {
	spec, ok := catalog.GetBuilding(building.TypeFieldBed)
	if !ok {
		t.Fatal("windleaf bed catalog entry not found")
	}
	if spec.BuildDuration != 40*time.Second || spec.Health != 70 {
		t.Fatalf("unexpected first windleaf bed level: %#v", spec)
	}
	if len(spec.UpgradeLevels) != 11 {
		t.Fatalf("expected 11 windleaf bed levels, got %d", len(spec.UpgradeLevels))
	}
	levelThree := spec.UpgradeLevels[2]
	if levelThree.BuildDuration != 20*time.Minute+5*time.Second || levelThree.Health != 170 {
		t.Fatalf("unexpected windleaf bed level 3: %#v", levelThree)
	}
	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 11 || final.BuildDuration != 10*time.Hour+25*time.Minute || final.Health != 1800 {
		t.Fatalf("unexpected final windleaf bed level: %#v", final)
	}
	if final.Cost[len(final.Cost)-1].Resource != "emerald_dust" || final.Cost[len(final.Cost)-1].Amount != 1 {
		t.Fatalf("expected emerald dust final cost, got %#v", final.Cost)
	}
}

func TestStartingInventoryCanPayForFirstLevelBuildings(t *testing.T) {
	inventory := economy.Inventory{Items: economy.StartingItems()}
	for _, spec := range catalog.FirstLevelBuildings() {
		if !inventory.Has(toEconomyCost(spec.Cost)) {
			t.Fatalf("starting inventory cannot pay for first-level building %s: cost %#v, inventory %#v", spec.Type, spec.Cost, inventory.Items)
		}
	}
}

func TestBuildingServiceRejectsOccupiedTilesAcrossPlayers(t *testing.T) {
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	if _, err := service.Place(context.Background(), PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatalf("place first town hall: %v", err)
	}
	if _, err := service.Place(context.Background(), PlaceBuildingInput{PlayerID: player.ID("p2"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err == nil {
		t.Fatal("expected occupied tile error for another player's building")
	}
}

func TestBuildingServiceRejectsMonsterOccupiedTile(t *testing.T) {
	ctx := context.Background()
	monsterRepo := memory.NewMonsterRepo()
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetMonsters(monsterRepo)
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeDugout, Tile: world.Coord{X: 10, Y: -3}}); err == nil {
		t.Fatal("expected monster occupied tile error")
	}
}

func TestBuildingServiceReturnsPopulationAfterConstructionCompletes(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	service := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetEconomy(economyService)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }
	economyService.now = func() time.Time { return now }
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	start, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	dugout, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeDugout, Tile: world.Coord{X: 4, Y: 4}})
	if err != nil {
		t.Fatalf("place dugout: %v", err)
	}
	reserved, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if reserved.Items[economy.ResourcePopulation] != start.Items[economy.ResourcePopulation]-1 {
		t.Fatalf("expected one reserved builder, got start=%d reserved=%d", start.Items[economy.ResourcePopulation], reserved.Items[economy.ResourcePopulation])
	}
	service.now = func() time.Time { return dugout.CompletesAt.Add(time.Second) }
	economyService.now = service.now
	if _, err := service.Complete(ctx, dugout.ID, player.ID("p1")); err != nil {
		t.Fatalf("complete dugout: %v", err)
	}
	completed, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if completed.Items[economy.ResourcePopulation] != start.Items[economy.ResourcePopulation] {
		t.Fatalf("expected population returned, got start=%d completed=%d", start.Items[economy.ResourcePopulation], completed.Items[economy.ResourcePopulation])
	}
}

func TestBuildingServiceRushCompleteSpendsCrystalsAndReturnsPopulation(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	service := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetEconomy(economyService)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }
	economyService.now = func() time.Time { return now }
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	start, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	dugout, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeDugout, Tile: world.Coord{X: 4, Y: 4}})
	if err != nil {
		t.Fatalf("place dugout: %v", err)
	}
	rushed, inventory, cost, err := service.RushComplete(ctx, dugout.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("rush complete: %v", err)
	}
	if cost != 1 {
		t.Fatalf("expected one crystal rush cost, got %d", cost)
	}
	if rushed.State != building.StateActive || rushed.CompletesAt != nil {
		t.Fatalf("expected active rushed building, got %#v", rushed)
	}
	if inventory.Items[economy.ResourceAeolianCrystal] != start.Items[economy.ResourceAeolianCrystal]-1 {
		t.Fatalf("expected one crystal spent, got start=%d after=%d", start.Items[economy.ResourceAeolianCrystal], inventory.Items[economy.ResourceAeolianCrystal])
	}
	if inventory.Items[economy.ResourcePopulation] != start.Items[economy.ResourcePopulation] {
		t.Fatalf("expected builder returned, got start=%d after=%d", start.Items[economy.ResourcePopulation], inventory.Items[economy.ResourcePopulation])
	}
}
