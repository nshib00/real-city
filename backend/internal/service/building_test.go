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

func TestStoneHouseUpgradeChainFollowsTargetLevelSpecs(t *testing.T) {
	wood, ok := catalog.GetBuilding(building.TypeWoodHouse)
	if !ok || len(wood.UpgradeLevels) != 6 {
		t.Fatal("wooden house six-level catalog missing")
	}
	current := building.Building{Type: building.TypeWoodHouse, Level: 6}
	for level := 1; level <= 6; level++ {
		next, ok := nextUpgrade(current)
		if !ok || next.Type != building.TypeStoneHouse || next.Level != level {
			t.Fatalf("transition to stone house level %d: %#v, ok=%v", level, next, ok)
		}
		if next.Health <= 3310 || next.BuildDuration <= 4*time.Hour || next.Population <= 20 || len(next.Cost) == 0 {
			t.Fatalf("incomplete balance for stone house level %d: %#v", level, next)
		}
		current.Type, current.Level = next.Type, next.Level
	}
	if _, ok := nextUpgrade(current); ok {
		t.Fatal("stone house branch must be selected explicitly")
	}
	for _, branch := range []building.Type{building.TypeVilla, building.TypeApartmentHouse} {
		next, ok := nextUpgradeTo(current, branch)
		if !ok || next.Type != branch || next.Level != 1 {
			t.Fatalf("stone house branch %s: %#v, ok=%v", branch, next, ok)
		}
	}
	if _, ok := nextUpgradeTo(current, building.TypePalace); ok {
		t.Fatal("stone house must reject a branch outside its catalog")
	}
	current.Type, current.Level = building.TypeVilla, 1
	next, ok := nextUpgradeTo(current, building.TypeVilla)
	if !ok || next.Type != building.TypeVilla || next.Level != 2 {
		t.Fatalf("villa should continue within its branch: %#v, ok=%v", next, ok)
	}
	if _, ok := nextUpgradeTo(current, building.TypeApartmentHouse); ok {
		t.Fatal("villa must not switch to apartment branch")
	}
}

func TestStoneHouseUpgradeChoicePersistsAsSelectedType(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	service := NewBuildingService(repo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	item := building.Building{ID: "stone-branch", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeStoneHouse,
		Name: "Каменный дом", Level: 6, State: building.StateActive, Health: 8700,
		Tile: world.Coord{X: 3, Y: 3}, Footprint: building.Footprint{Width: 1, Height: 1}}
	if err := repo.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if _, err := service.Upgrade(ctx, item.ID, "p1"); err == nil {
		t.Fatal("branch selection must be required")
	}
	if _, err := service.UpgradeTo(ctx, item.ID, "p1", building.TypePalace); err == nil {
		t.Fatal("unlisted target must be rejected")
	}
	upgraded, err := service.UpgradeTo(ctx, item.ID, "p1", building.TypeVilla)
	if err != nil {
		t.Fatal(err)
	}
	if upgraded.Type != building.TypeVilla || upgraded.Level != 1 || upgraded.Health != 9500 {
		t.Fatalf("selected branch was not saved: %#v", upgraded)
	}
	stored, err := repo.FindByID(ctx, item.ID)
	if err != nil {
		t.Fatal(err)
	}
	if stored.Type != building.TypeVilla {
		t.Fatalf("stored branch = %s", stored.Type)
	}
}

func TestStoneHouseCannotBePlacedDirectly(t *testing.T) {
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	_, err := service.Place(context.Background(), PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeStoneHouse, Tile: world.Coord{X: 4, Y: 4}})
	if err == nil {
		t.Fatal("stone house must be reached through wooden house level 6")
	}
}

func TestBuildingRelocationChecksOwnershipAndFootprint(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	worlds := memory.NewWorldRepo()
	service := NewBuildingService(repo, worlds, slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 10, 24, 12, 0, 0, 0, time.UTC)
	service.SetNowForTest(func() time.Time { return now })
	_, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkCoord{})
	if err != nil {
		t.Fatal(err)
	}
	for y := 4; y < 9; y++ {
		for x := 4; x < 10; x++ {
			coord := world.Coord{X: x, Y: y}
			if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: coord, Chunk: world.ChunkForTile(coord), Terrain: world.TerrainGrass}); err != nil {
				t.Fatal(err)
			}
		}
	}
	item := building.Building{ID: "moving", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeWoodHouse,
		Level: 1, State: building.StateActive, Health: 200, Tile: world.Coord{X: 4, Y: 4},
		Footprint: building.Footprint{Width: 2, Height: 1}, UpdatedAt: now.Add(-time.Second)}
	blocker := building.Building{ID: "blocker", MapID: DefaultWorldID, OwnerID: "p2", Type: building.TypeDugout,
		State: building.StateActive, Tile: world.Coord{X: 7, Y: 5}, Footprint: building.Footprint{Width: 1, Height: 1}}
	for _, b := range []building.Building{item, blocker} {
		if err := repo.Create(ctx, b); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := service.Relocate(ctx, item.ID, "p2", world.Coord{X: 6, Y: 5}, 0); err == nil {
		t.Fatal("another player relocated the building")
	}
	if _, err := service.Relocate(ctx, item.ID, "p1", world.Coord{X: 7, Y: 5}, 0); err == nil {
		t.Fatal("relocation overlapped another building")
	}
	if _, err := service.Relocate(ctx, item.ID, "p1", world.Coord{X: 4, Y: 4}, 4); err == nil {
		t.Fatal("invalid rotation was accepted")
	}
	forest := world.Coord{X: 8, Y: 6}
	if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: forest, Chunk: world.ChunkForTile(forest), Terrain: world.TerrainForest}); err != nil {
		t.Fatal(err)
	}
	if _, err := service.Relocate(ctx, item.ID, "p1", forest, 0); err == nil {
		t.Fatal("relocation onto forest was accepted")
	}
	moved, err := service.Relocate(ctx, item.ID, "p1", world.Coord{X: 5, Y: 5}, 1)
	if err != nil {
		t.Fatal(err)
	}
	if moved.Tile != (world.Coord{X: 5, Y: 5}) || moved.Rotation != 1 || moved.Footprint != (building.Footprint{Width: 1, Height: 2}) {
		t.Fatalf("unexpected relocated building: %#v", moved)
	}
	stored, err := repo.FindByID(ctx, item.ID)
	if err != nil || stored.Tile != moved.Tile || stored.Footprint != moved.Footprint {
		t.Fatalf("relocation not persisted: %#v, %v", stored, err)
	}
	if _, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(world.Coord{X: 159, Y: 5})); err != nil {
		t.Fatal(err)
	}
	for _, coord := range []world.Coord{{X: 159, Y: 5}, {X: 0, Y: 5}} {
		if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: coord, Chunk: world.ChunkForTile(coord), Terrain: world.TerrainGrass}); err != nil {
			t.Fatal(err)
		}
	}
	if err := repo.Create(ctx, building.Building{ID: "seam-blocker", MapID: DefaultWorldID, OwnerID: "p2",
		Type: building.TypeDugout, State: building.StateActive, Tile: world.Coord{X: 0, Y: 5},
		Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
		t.Fatal(err)
	}
	if _, err := service.Relocate(ctx, item.ID, "p1", world.Coord{X: 159, Y: 5}, 2); err == nil {
		t.Fatal("relocation across the world seam overlapped another building")
	}
}

func TestBuildingRelocationNotifiesAllOldAndNewFootprintChunks(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewBuildingRepo()
	worlds := memory.NewWorldRepo()
	service := NewBuildingService(repo, worlds, slog.New(slog.NewTextHandler(io.Discard, nil)))
	events := NewEventBus(8)
	service.SetEventBus(events)
	stream := events.Subscribe(ctx)
	for _, coord := range []world.Coord{{X: 64, Y: 5}, {X: 65, Y: 5}} {
		if _, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(coord)); err != nil {
			t.Fatal(err)
		}
		if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: coord, Chunk: world.ChunkForTile(coord), Terrain: world.TerrainGrass}); err != nil {
			t.Fatal(err)
		}
	}
	item := building.Building{ID: "moving", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeWoodHouse,
		State: building.StateActive, Tile: world.Coord{X: 31, Y: 5}, Footprint: building.Footprint{Width: 2, Height: 1}}
	if err := repo.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if _, err := service.Relocate(ctx, item.ID, "p1", world.Coord{X: 64, Y: 5}, 0); err != nil {
		t.Fatal(err)
	}
	got := map[string]EventType{}
	for i := 0; i < 3; i++ {
		select {
		case event := <-stream:
			got[event.ChunkID] = event.Type
		default:
			t.Fatalf("expected three chunk events, got %v", got)
		}
	}
	for chunk, kind := range map[string]EventType{
		"dev-world:0:0": EventBuildingRemoved,
		"dev-world:1:0": EventBuildingRemoved,
		"dev-world:2:0": EventBuildingUpdated,
	} {
		if got[chunk] != kind {
			t.Fatalf("chunk %s: event %s, want %s", chunk, got[chunk], kind)
		}
	}
}

func TestRepairRestoresCurrentLevelHealth(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	service := NewBuildingService(repo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	item := building.Building{ID: "damaged", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeStoneHouse,
		Level: 6, State: building.StateDamaged, Health: 100, Footprint: building.Footprint{Width: 1, Height: 1}}
	if err := repo.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	eco := NewEconomyService(memory.NewEconomyRepo(), repo, slog.Default())
	service.SetEconomy(eco)
	quote := quoteRepair(item)
	grant := []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: 3}}
	for _, cost := range quote.Cost {
		grant = append(grant, economy.ResourceAmount{Resource: cost.Resource, Amount: cost.Amount})
	}
	grantTestResources(t, withUncappedCoins(ctx), eco, "p1", grant...)
	repaired, err := service.Repair(ctx, item.ID, "p1")
	if err != nil {
		t.Fatal(err)
	}
	if repaired.Health != 100 {
		t.Fatal("repair healed before timer")
	}
	if _, err = service.Repair(ctx, item.ID, "p1"); err == nil {
		t.Fatal("duplicate repair accepted")
	}
	pending, _ := repo.PendingRepair(ctx, item.ID)
	if n, err := service.CompleteRepairs(ctx, pending.DueAt.Add(time.Second), 10); err != nil || n != 1 {
		t.Fatalf("complete repair: %d %v", n, err)
	}
	repaired, err = repo.FindByID(ctx, item.ID)
	if err != nil {
		t.Fatal(err)
	}
	if repaired.Health != 8700 || repaired.State != building.StateActive {
		t.Fatalf("incorrect level 6 repair: %#v", repaired)
	}
	if _, err := service.Repair(ctx, item.ID, "p1"); err == nil {
		t.Fatal("repairing an intact building should fail")
	}
}

func TestBuildingServiceListsNearbyBuildingsAcrossOwners(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	service := NewBuildingService(repo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	for _, item := range []building.Building{
		{ID: "own", MapID: DefaultWorldID, OwnerID: "p1", Tile: world.Coord{X: 4, Y: 4}},
		{ID: "foreign", MapID: DefaultWorldID, OwnerID: "p2", Tile: world.Coord{X: 34, Y: 4}},
		{ID: "distant", MapID: DefaultWorldID, OwnerID: "p2", Tile: world.Coord{X: 96, Y: 4}},
	} {
		if err := repo.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	items, err := service.ListNearby(ctx, world.ChunkCoord{X: 0, Y: 0}, 1)
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 2 || items[0].ID != "own" || items[1].ID != "foreign" {
		t.Fatalf("nearby buildings = %#v", items)
	}
	if _, err := service.ListNearby(ctx, world.ChunkCoord{}, 4); err == nil {
		t.Fatal("expected radius validation error")
	}
}

func TestBuildingServiceListsBuildingsAcrossDistrictAndWorldEdges(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	service := NewBuildingService(repo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	for _, item := range []building.Building{
		{ID: "current", MapID: DefaultWorldID, Tile: world.Coord{X: 0, Y: 0}},
		{ID: "west", MapID: DefaultWorldID, Tile: world.Coord{X: 159, Y: 0}},
		{ID: "north", MapID: DefaultWorldID, Tile: world.Coord{X: 0, Y: 159}},
		{ID: "corner", MapID: DefaultWorldID, Tile: world.Coord{X: 159, Y: 159}},
		{ID: "next-district", MapID: DefaultWorldID, Tile: world.Coord{X: 32, Y: 0}},
		{ID: "far", MapID: DefaultWorldID, Tile: world.Coord{X: 96, Y: 96}},
	} {
		if err := repo.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	items, err := service.ListNearby(ctx, world.ChunkCoord{X: 0, Y: 0}, 1)
	if err != nil {
		t.Fatal(err)
	}
	seen := make(map[string]int)
	for _, item := range items {
		seen[string(item.ID)]++
	}
	for _, id := range []string{"current", "west", "north", "corner", "next-district"} {
		if seen[id] != 1 {
			t.Fatalf("building %s appeared %d times", id, seen[id])
		}
	}
	if seen["far"] != 0 {
		t.Fatalf("distant building appeared in viewport")
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
	if len(spec.UpgradeLevels) != 15 {
		t.Fatalf("expected 15 town hall levels, got %d", len(spec.UpgradeLevels))
	}
	for _, level := range spec.UpgradeLevels {
		if level.Population != 3 {
			t.Fatalf("town hall population must stay 3 on every level, got level %d: %d", level.Level, level.Population)
		}
	}

	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 15 || final.Health != 8750 || final.BuildDuration != 33*time.Hour {
		t.Fatalf("unexpected final town hall level: %#v", final)
	}
	if got := (building.BuildRules{BaseLimit: 8}).LimitForTownHallLevel(15); got != 50 {
		t.Fatalf("expected level 15 town hall limit 50, got %d", got)
	}
}

func TestBuildingServiceCompletesTownHallUpgradesThroughLevel15(t *testing.T) {
	ctx := context.Background()
	service := NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 10, 31, 12, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }
	item, err := service.Place(ctx, PlaceBuildingInput{PlayerID: "p1", Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}})
	if err != nil {
		t.Fatal(err)
	}
	for level := 2; level <= 15; level++ {
		item, err = service.Upgrade(ctx, item.ID, "p1")
		if err != nil {
			t.Fatalf("upgrade to %d: %v", level, err)
		}
		if item.Level != level || item.CompletesAt == nil || item.State != building.StateBuilding {
			t.Fatalf("invalid upgrade to %d: %#v", level, item)
		}
		now = item.CompletesAt.Add(time.Second)
		item, err = service.Complete(ctx, item.ID, "p1")
		if err != nil {
			t.Fatalf("complete %d: %v", level, err)
		}
		if item.State != building.StateActive || item.Health <= 0 {
			t.Fatalf("invalid completed level %d: %#v", level, item)
		}
		if catalog.ExperienceForBuilding(building.TypeTownHall, level).Completion <= 0 {
			t.Fatalf("missing XP for %d", level)
		}
	}
	if _, err := service.Upgrade(ctx, item.ID, "p1"); err == nil {
		t.Fatal("level 15 must be final")
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

func TestStartingInventoryGrantsCoinsAndThrowingKnives(t *testing.T) {
	items := economy.StartingItems()
	if len(items) != 2 {
		t.Fatalf("expected two starting resources, got %#v", items)
	}
	if items[economy.ResourceCoins] != 50 {
		t.Fatalf("expected 50 starting coins, got %#v", items)
	}
	if items[economy.ResourceThrowingKnives] != 50 {
		t.Fatalf("expected 50 starting throwing knives, got %#v", items)
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

func TestTownHallDoesNotRestoreReservedPopulation(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	buildingService := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	buildingService.SetEconomy(economyService)
	if _, err := buildingService.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatal(err)
	}
	for _, expected := range []int{2, 1, 0} {
		if _, err := economyService.Spend(ctx, player.ID("p1"), []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: 1}}, "test:workers"); err != nil {
			t.Fatal(err)
		}
		inventory, err := economyService.Inventory(ctx, player.ID("p1"))
		if err != nil {
			t.Fatal(err)
		}
		if inventory.Items[economy.ResourcePopulation] != expected {
			t.Fatalf("expected %d free population, got %d", expected, inventory.Items[economy.ResourcePopulation])
		}
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
	for _, costs := range [][]building.Cost{spec.Cost, spec.UpgradeLevels[0].Cost} {
		if len(costs) != 3 || costs[0].Resource != "coins" || costs[0].Amount != 1500 || costs[1].Resource != "wood" || costs[1].Amount != 70 || costs[2].Resource != "planks" || costs[2].Amount != 15 {
			t.Fatalf("unexpected first coin storage level cost: %#v", costs)
		}
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

func TestClayQuarryCatalogUsesDocumentedUpgradeBalance(t *testing.T) {
	spec, ok := catalog.GetBuilding(building.TypeClayQuarry)
	if !ok || spec.BuildDuration != 7*time.Minute || spec.Health != 95 || spec.Population != 3 {
		t.Fatalf("unexpected first clay quarry level: %#v", spec)
	}
	if len(spec.UpgradeLevels) != 12 {
		t.Fatalf("expected 12 clay quarry levels, got %d", len(spec.UpgradeLevels))
	}
	for index, level := range spec.UpgradeLevels {
		if level.Level != index+1 {
			t.Fatalf("unexpected clay quarry level %d: %#v", index+1, level)
		}
	}
	seventh := spec.UpgradeLevels[6]
	if seventh.BuildDuration != 6*time.Hour+45*time.Minute || seventh.Population != 13 || seventh.Health != 1190 {
		t.Fatalf("unexpected fuel-powered clay quarry level: %#v", seventh)
	}
	final := spec.UpgradeLevels[11]
	if final.BuildDuration != 28*time.Hour || final.Population != 24 || final.Health != 2780 || final.Cost[0].Amount != 2180000 {
		t.Fatalf("unexpected final clay quarry level: %#v", final)
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
	if len(spec.UpgradeLevels) != 12 {
		t.Fatalf("expected 12 glass workshop levels, got %d", len(spec.UpgradeLevels))
	}
	levelFive := spec.UpgradeLevels[4]
	if levelFive.BuildDuration != 5*time.Hour+14*time.Minute+20*time.Second || levelFive.Health != 1412 {
		t.Fatalf("unexpected glass workshop level 5: %#v", levelFive)
	}
	final := spec.UpgradeLevels[len(spec.UpgradeLevels)-1]
	if final.Level != 12 || final.BuildDuration != 28*time.Hour || final.Health != 4500 {
		t.Fatalf("unexpected final glass workshop level: %#v", final)
	}
	if final.Cost[len(final.Cost)-1].Resource != "star_glass" || final.Cost[len(final.Cost)-1].Amount != 4 {
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

func TestBuildingServiceReturnsPopulationWhenConstructionIsDemolished(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	service := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetEconomy(economyService)
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatal(err)
	}
	start := grantTestResources(t, ctx, economyService, player.ID("p1"), economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 3})
	dugout, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeDugout, Tile: world.Coord{X: 4, Y: 4}})
	if err != nil {
		t.Fatal(err)
	}
	reserved, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if reserved.Items[economy.ResourcePopulation] != start.Items[economy.ResourcePopulation]-1 {
		t.Fatalf("expected one reserved builder, got %d", reserved.Items[economy.ResourcePopulation])
	}
	if err := service.Demolish(ctx, dugout.ID, player.ID("p1")); err != nil {
		t.Fatal(err)
	}
	returned, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if returned.Items[economy.ResourcePopulation] != start.Items[economy.ResourcePopulation] {
		t.Fatalf("expected builder to return after demolition, got %d", returned.Items[economy.ResourcePopulation])
	}
}

func TestDemolishWorkingFieldReturnsWorkersAndOnlyCoins(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	repository := memory.NewEconomyRepo()
	economyService := NewEconomyService(repository, buildings, slog.Default())
	service := NewBuildingService(buildings, memory.NewWorldRepo(), slog.Default())
	service.SetEconomy(economyService)
	now := time.Now().UTC()
	readyAt := now.Add(time.Hour)
	item := building.Building{ID: "working-field", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeFieldBed, Level: 1, State: building.StateActive, FieldStage: 2, FieldStageStartedAt: &now, FieldStageReadyAt: &readyAt}
	if err := buildings.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	grantTestResources(t, ctx, economyService, "p1", economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 2}, economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 10})
	if _, err := economyService.Spend(ctx, "p1", []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: 1}}, "test:field:workers"); err != nil {
		t.Fatal(err)
	}
	if err := service.Demolish(ctx, item.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	returned, err := economyService.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	if returned.Items[economy.ResourcePopulation] != 2 || returned.Items[economy.ResourceWood] != 10 || returned.Items[economy.ResourceCoins] != 50+catalog.DemolitionRefundCoins(item.Type, item.Level) {
		t.Fatalf("unexpected demolition refund: %#v", returned.Items)
	}
	if _, err := buildings.FindByID(ctx, item.ID); err == nil {
		t.Fatal("demolished field still exists")
	}
}

func TestDemolishRunningProductionReturnsWorkersAndCancelsJob(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	repository := memory.NewEconomyRepo()
	economyService := NewEconomyService(repository, buildings, slog.Default())
	service := NewBuildingService(buildings, memory.NewWorldRepo(), slog.Default())
	service.SetEconomy(economyService)
	item := building.Building{ID: "working-sawmill", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeLumberYard, Level: 1, State: building.StateActive}
	if err := buildings.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	recipe, ok := catalog.RecipeForBuildingLevel("planks_from_wood", 1)
	if !ok {
		t.Fatal("missing sawmill recipe")
	}
	grantTestResources(t, ctx, economyService, "p1", economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: recipe.Workers + 1})
	if _, err := economyService.Spend(ctx, "p1", []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: recipe.Workers}}, "test:production:workers"); err != nil {
		t.Fatal(err)
	}
	job := economy.ProductionJob{ID: "job-1", PlayerID: "p1", BuildingID: string(item.ID), RecipeID: recipe.ID, State: economy.ProductionRunning}
	if err := repository.SaveProductionJob(ctx, job); err != nil {
		t.Fatal(err)
	}
	if err := service.Demolish(ctx, item.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	returned, err := economyService.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	storedJob, err := repository.FindProductionJob(ctx, job.ID)
	if err != nil {
		t.Fatal(err)
	}
	if returned.Items[economy.ResourcePopulation] != recipe.Workers+1 || storedJob.State != economy.ProductionCancelled {
		t.Fatalf("unexpected production demolition: population=%d job=%s", returned.Items[economy.ResourcePopulation], storedJob.State)
	}
}

func TestDemolitionRefundIsNotLostAtCoinCapacity(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	economyService := NewEconomyService(memory.NewEconomyRepo(), buildings, slog.Default())
	service := NewBuildingService(buildings, memory.NewWorldRepo(), slog.Default())
	service.SetEconomy(economyService)
	item := building.Building{ID: "coin-storage-test", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeCoinStorage, Level: 1, State: building.StateActive}
	if err := buildings.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	starting := grantTestResources(t, ctx, economyService, "p1", economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: 2000})
	if err := service.Demolish(ctx, item.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	returned, err := economyService.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	want := starting.Items[economy.ResourceCoins] + catalog.DemolitionRefundCoins(item.Type, item.Level)
	if returned.Items[economy.ResourceCoins] != want {
		t.Fatalf("refund was capped: got %d, want %d", returned.Items[economy.ResourceCoins], want)
	}
}

func TestPlannedBuildingsDoNotReturnUnreservedPopulation(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	service := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetEconomy(economyService)
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatal(err)
	}
	for _, id := range []building.ID{"planned-cancel", "planned-rush"} {
		if err := buildingRepo.Create(ctx, building.Building{ID: id, MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeDugout, Level: 1, State: building.StatePlanned}); err != nil {
			t.Fatal(err)
		}
	}
	if err := service.Cancel(ctx, "planned-cancel", player.ID("p1")); err != nil {
		t.Fatal(err)
	}
	if _, _, _, err := service.RushComplete(ctx, "planned-rush", player.ID("p1")); err != nil {
		t.Fatal(err)
	}
	inventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if inventory.Items[economy.ResourcePopulation] != 3 {
		t.Fatalf("planned buildings must not create free residents, got %d", inventory.Items[economy.ResourcePopulation])
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
