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
	if spec.Population != 3 {
		t.Fatalf("expected level 1 town hall to grant 3 population, got %d", spec.Population)
	}
	if len(spec.UpgradeLevels) != 10 {
		t.Fatalf("expected 10 town hall levels, got %d", len(spec.UpgradeLevels))
	}
	for _, level := range spec.UpgradeLevels {
		if level.Population != 3 {
			t.Fatalf("town hall population must stay 3 on every level, got level %d: %d", level.Level, level.Population)
		}
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

func TestStartingInventoryOnlyGrantsCoins(t *testing.T) {
	items := economy.StartingItems()
	if len(items) != 1 {
		t.Fatalf("expected only one starting resource, got %#v", items)
	}
	if items[economy.ResourceCoins] != 50 {
		t.Fatalf("expected 50 starting coins, got %#v", items)
	}
}

func TestTownHallGrantsStarterPopulation(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	service := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetEconomy(economyService)
	now := time.Date(2026, 10, 10, 12, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }
	economyService.now = func() time.Time { return now }

	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	inventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if inventory.Items[economy.ResourcePopulation] != 3 {
		t.Fatalf("expected town hall to grant 3 starter population, got %d", inventory.Items[economy.ResourcePopulation])
	}
}

func TestInventoryBackfillsStarterPopulationForExistingTownHall(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 10, 10, 12, 0, 0, 0, time.UTC)
	economyService.now = func() time.Time { return now }
	if err := buildingRepo.Create(ctx, building.Building{
		ID:        "town-hall-existing",
		MapID:     DefaultWorldID,
		OwnerID:   "p1",
		Type:      building.TypeTownHall,
		Name:      "Ратуша",
		Level:     1,
		State:     building.StateActive,
		Health:    100,
		Tile:      world.Coord{X: 0, Y: 0},
		Footprint: building.Footprint{Width: 2, Height: 2},
		StartedAt: now,
		CreatedAt: now,
		UpdatedAt: now,
	}); err != nil {
		t.Fatal(err)
	}

	inventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if inventory.Items[economy.ResourcePopulation] != 3 {
		t.Fatalf("expected existing town hall to backfill 3 starter population, got %d", inventory.Items[economy.ResourcePopulation])
	}

	stored, err := economyRepo.GetInventory(ctx, player.ID("p1"), BaseCoinCapacity)
	if err != nil {
		t.Fatal(err)
	}
	if stored.Items[economy.ResourcePopulation] != 3 {
		t.Fatalf("expected backfilled population to be saved, got %d", stored.Items[economy.ResourcePopulation])
	}
}

func TestCoinStorageCatalogUsesDocumentedUpgradeBalance(t *testing.T) {
	spec, ok := catalog.GetBuilding(building.TypeCoinStorage)
	if !ok {
		t.Fatal("coin storage catalog entry not found")
	}
	if spec.BuildDuration != 7*time.Minute || spec.Population != 5 || spec.Health != 400 {
		t.Fatalf("unexpected first coin storage level: %#v", spec)
	}
	if len(spec.UpgradeLevels) != 12 {
		t.Fatalf("expected 12 coin storage levels, got %d", len(spec.UpgradeLevels))
	}
	levelThree := spec.UpgradeLevels[2]
	if levelThree.BuildDuration != 72*time.Minute || levelThree.Population != 12 || levelThree.Health != 1200 {
		t.Fatalf("unexpected coin storage level 3: %#v", levelThree)
	}
	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 12 || final.BuildDuration != 38*time.Hour+30*time.Minute || final.Population != 93 || final.Health != 15500 {
		t.Fatalf("unexpected final coin storage level: %#v", final)
	}
}

func TestWallAndRoadCatalogConnectsUpgradeChains(t *testing.T) {
	woodenWall, _ := catalog.GetBuilding(building.TypeWoodenWall)
	if len(woodenWall.UpgradeLevels) != 3 || woodenWall.UpgradeLevels[2].NextType != building.TypeStoneWall {
		t.Fatalf("wooden wall should upgrade through level 3 into stone wall: %#v", woodenWall.UpgradeLevels)
	}
	stoneWall, _ := catalog.GetBuilding(building.TypeStoneWall)
	if len(stoneWall.UpgradeLevels) != 4 || stoneWall.UpgradeLevels[3].NextType != building.TypeConcreteWall {
		t.Fatalf("stone wall should upgrade through level 7 into concrete wall: %#v", stoneWall.UpgradeLevels)
	}
	concreteWall, _ := catalog.GetBuilding(building.TypeConcreteWall)
	if len(concreteWall.UpgradeLevels) != 3 || concreteWall.UpgradeLevels[2].NextType != building.TypeModernWall {
		t.Fatalf("concrete wall should upgrade through level 10 into modern wall: %#v", concreteWall.UpgradeLevels)
	}
	modernWall, _ := catalog.GetBuilding(building.TypeModernWall)
	if len(modernWall.UpgradeLevels) != 3 || modernWall.UpgradeLevels[2].Level != 13 {
		t.Fatalf("modern wall should expose levels 11-13: %#v", modernWall.UpgradeLevels)
	}

	groundRoad, _ := catalog.GetBuilding(building.TypeRoad)
	if len(groundRoad.UpgradeLevels) != 1 || groundRoad.UpgradeLevels[0].NextType != building.TypeStandardRoad {
		t.Fatalf("ground road should upgrade into standard road: %#v", groundRoad.UpgradeLevels)
	}
	standardRoad, _ := catalog.GetBuilding(building.TypeStandardRoad)
	if len(standardRoad.UpgradeLevels) != 1 || standardRoad.UpgradeLevels[0].NextType != building.TypePavedRoad {
		t.Fatalf("standard road should upgrade into paved road: %#v", standardRoad.UpgradeLevels)
	}
}

func TestEconomyCoinCapacityUsesActiveCoinStorageLevels(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyService := NewEconomyService(memory.NewEconomyRepo(), buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 9, 29, 12, 0, 0, 0, time.UTC)

	items := []building.Building{
		{ID: "coin-storage-l1", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeCoinStorage, Name: "Хранилище монет", Level: 1, State: building.StateActive, Health: 400, Tile: world.Coord{X: 1, Y: 1}, Footprint: building.Footprint{Width: 1, Height: 1}, CreatedAt: now, UpdatedAt: now},
		{ID: "coin-storage-l3", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeCoinStorage, Name: "Хранилище монет", Level: 3, State: building.StateDamaged, Health: 100, Tile: world.Coord{X: 2, Y: 1}, Footprint: building.Footprint{Width: 1, Height: 1}, CreatedAt: now, UpdatedAt: now},
		{ID: "coin-storage-building", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeCoinStorage, Name: "Хранилище монет", Level: 12, State: building.StateBuilding, Health: 15500, Tile: world.Coord{X: 3, Y: 1}, Footprint: building.Footprint{Width: 1, Height: 1}, CreatedAt: now, UpdatedAt: now},
	}
	for _, item := range items {
		if err := buildingRepo.Create(ctx, item); err != nil {
			t.Fatalf("create building: %v", err)
		}
	}

	capacity, err := economyService.CoinCapacity(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if capacity != BaseCoinCapacity+2000+10000 {
		t.Fatalf("expected active and damaged storages to add documented capacity, got %d", capacity)
	}
}

func TestMineCatalogUsesDocumentedUpgradeBalance(t *testing.T) {
	spec, ok := catalog.GetBuilding(building.TypeMine)
	if !ok {
		t.Fatal("mine catalog entry not found")
	}
	if spec.BuildDuration != 12*time.Minute || spec.Health != 176 {
		t.Fatalf("unexpected first mine level: %#v", spec)
	}
	if len(spec.UpgradeLevels) != 12 {
		t.Fatalf("expected 12 mine levels, got %d", len(spec.UpgradeLevels))
	}
	levelNine := spec.UpgradeLevels[8]
	if levelNine.BuildDuration != 10*time.Hour+35*time.Minute || levelNine.Health != 2003 {
		t.Fatalf("unexpected mine level 9: %#v", levelNine)
	}
	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 12 || final.BuildDuration != 22*time.Hour+24*time.Minute || final.Health != 3005 {
		t.Fatalf("unexpected final mine level: %#v", final)
	}
	if final.Cost[1].Resource != "armor_plates" || final.Cost[1].Amount != 2 {
		t.Fatalf("expected protective plate final cost, got %#v", final.Cost)
	}
}

func TestGlassWorkshopCatalogUsesDocumentedUpgradeBalance(t *testing.T) {
	spec, ok := catalog.GetBuilding(building.TypeGlassWorkshop)
	if !ok {
		t.Fatal("glass workshop catalog entry not found")
	}
	if spec.BuildDuration != 20*time.Minute || spec.Health != 436 || spec.Population != 6 {
		t.Fatalf("unexpected first glass workshop level: %#v", spec)
	}
	if len(spec.UpgradeLevels) != 9 {
		t.Fatalf("expected 9 glass workshop levels, got %d", len(spec.UpgradeLevels))
	}
	levelFive := spec.UpgradeLevels[4]
	if levelFive.BuildDuration != 5*time.Hour+14*time.Minute+20*time.Second || levelFive.Health != 1412 {
		t.Fatalf("unexpected glass workshop level 5: %#v", levelFive)
	}
	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 9 || final.BuildDuration != 15*time.Hour+30*time.Minute+30*time.Second || final.Health != 2810 {
		t.Fatalf("unexpected final glass workshop level: %#v", final)
	}
	if final.Cost[len(final.Cost)-1].Resource != "star_glass" || final.Cost[len(final.Cost)-1].Amount != 1 {
		t.Fatalf("expected star glass final cost, got %#v", final.Cost)
	}
}

func TestSandQuarryCatalogUsesDocumentedUpgradeBalance(t *testing.T) {
	spec, ok := catalog.GetBuilding(building.TypeSandQuarry)
	if !ok {
		t.Fatal("sand quarry catalog entry not found")
	}
	if spec.BuildDuration != 6*time.Minute+30*time.Second || spec.Health != 84 {
		t.Fatalf("unexpected first sand quarry level: %#v", spec)
	}
	if len(spec.UpgradeLevels) != 11 {
		t.Fatalf("expected 11 sand quarry levels, got %d", len(spec.UpgradeLevels))
	}
	levelNine := spec.UpgradeLevels[8]
	if levelNine.BuildDuration != 13*time.Hour+2*time.Minute || levelNine.Health != 1685 {
		t.Fatalf("unexpected sand quarry level 9: %#v", levelNine)
	}
	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 11 || final.BuildDuration != 0 || final.Health != 2055 {
		t.Fatalf("unexpected final sand quarry level: %#v", final)
	}
	if final.Cost[3].Resource != "blue_salt" || final.Cost[3].Amount != 5 {
		t.Fatalf("expected blue salt final cost, got %#v", final.Cost)
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

func TestBuildingServiceRejectsManagementActionsFromAnotherPlayer(t *testing.T) {
	ctx := context.Background()
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	townHall, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}})
	if err != nil {
		t.Fatalf("place town hall: %v", err)
	}

	if _, err := service.Upgrade(ctx, townHall.ID, player.ID("p2")); err == nil {
		t.Fatal("expected another player upgrade to be rejected")
	}
	if _, _, _, err := service.RushComplete(ctx, townHall.ID, player.ID("p2")); err == nil {
		t.Fatal("expected another player rush complete to be rejected")
	}
	if err := service.Demolish(ctx, townHall.ID, player.ID("p2")); err == nil {
		t.Fatal("expected another player demolish to be rejected")
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
	grantTestResources(t, ctx, economyService, player.ID("p1"),
		economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 3},
		economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 1},
	)
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

func TestBuildingServiceDoesNotAutoStartWindleafBedAfterConstruction(t *testing.T) {
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
	grantTestResources(t, ctx, economyService, player.ID("p1"),
		economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: 250},
		economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 4},
		economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 1},
	)
	bed, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeFieldBed, Tile: world.Coord{X: 4, Y: 4}})
	if err != nil {
		t.Fatalf("place windleaf bed: %v", err)
	}
	service.now = func() time.Time { return bed.CompletesAt.Add(time.Second) }
	economyService.now = service.now
	completed, err := service.Complete(ctx, bed.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("complete windleaf bed: %v", err)
	}
	if completed.State != building.StateActive || completed.FieldStage != 0 || completed.FieldStageStartedAt != nil || completed.FieldStageReadyAt != nil {
		t.Fatalf("windleaf bed should be idle after construction, got %#v", completed)
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
	grantTestResources(t, ctx, economyService, player.ID("p1"),
		economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 3},
		economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 1},
		economy.ResourceAmount{Resource: economy.ResourceAeolianCrystal, Amount: 1},
	)
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

func grantTestResources(t *testing.T, ctx context.Context, service *EconomyService, playerID player.ID, items ...economy.ResourceAmount) economy.Inventory {
	t.Helper()
	inventory, _, err := service.Add(ctx, playerID, items, "test:grant")
	if err != nil {
		t.Fatal(err)
	}
	return inventory
}
