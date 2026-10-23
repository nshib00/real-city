package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func TestProductionServiceReservesAndReleasesPopulationWhenJobBecomesReady(t *testing.T) {
	ctx := context.Background()
	buildingRepo, economyRepo, economyService, productionService := newProductionPopulationTestServices()
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	economyService.now = func() time.Time { return now }
	productionService.now = func() time.Time { return now }
	createActiveProductionBuilding(t, ctx, buildingRepo, "lumber-1", player.ID("p1"), building.TypeLumberYard, 1)

	startInventory := setTestPopulation(t, ctx, economyRepo, economyService, player.ID("p1"), 10)
	job, inventory, err := productionService.Start(ctx, player.ID("p1"), "lumber-1", "planks_from_wood")
	if err != nil {
		t.Fatalf("start production: %v", err)
	}
	if inventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation]-3 {
		t.Fatalf("expected three workers reserved, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], inventory.Items[economy.ResourcePopulation])
	}

	now = job.CompletesAt.Add(time.Second)
	if _, err := productionService.ReadyAt(ctx, player.ID("p1"), job.ID, now); err != nil {
		t.Fatalf("mark production ready: %v", err)
	}
	readyInventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if readyInventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation] {
		t.Fatalf("expected workers released after ready, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], readyInventory.Items[economy.ResourcePopulation])
	}
}

func TestLumberYardConsumesFuelAndAwardsPremiumPlank(t *testing.T) {
	ctx := context.Background()
	buildings, repo, economyService, productionService := newProductionPopulationTestServices()
	createActiveProductionBuilding(t, ctx, buildings, "lumber-premium", player.ID("p1"), building.TypeLumberYard, 4)
	inventory := setTestPopulation(t, ctx, repo, economyService, player.ID("p1"), 20)
	inventory.Items[economy.ResourceFuel] = 5
	if err := repo.SaveInventory(ctx, inventory); err != nil {
		t.Fatal(err)
	}
	productionService.randFloat = func() float64 { return 0 }
	job, afterStart, err := productionService.Start(ctx, player.ID("p1"), "lumber-premium", "planks_from_wood")
	if err != nil {
		t.Fatal(err)
	}
	if afterStart.Items[economy.ResourceWood] != 76 || afterStart.Items[economy.ResourceFuel] != 0 || job.CompletesAt.Sub(job.StartedAt) != 1395*time.Second {
		t.Fatalf("unexpected cost or duration: inventory=%#v job=%#v", afterStart.Items, job)
	}
	_, afterCollect, err := productionService.CompleteAt(ctx, player.ID("p1"), job.ID, job.CompletesAt)
	if err != nil {
		t.Fatal(err)
	}
	if afterCollect.Items[economy.ResourcePlanks] != inventory.Items[economy.ResourcePlanks]+11 || afterCollect.Items[economy.ResourcePremiumPlanks] != inventory.Items[economy.ResourcePremiumPlanks]+1 {
		t.Fatalf("unexpected sawmill output: %#v", afterCollect.Items)
	}
}

func TestClayQuarryConsumesFuelAndAwardsKaolin(t *testing.T) {
	ctx := context.Background()
	buildings, repo, economyService, productionService := newProductionPopulationTestServices()
	createActiveProductionBuilding(t, ctx, buildings, "clay-1", player.ID("p1"), building.TypeClayQuarry, 7)
	inventory := setTestPopulation(t, ctx, repo, economyService, player.ID("p1"), 30)
	inventory.Items[economy.ResourceFuel] = 8
	if err := repo.SaveInventory(ctx, inventory); err != nil {
		t.Fatal(err)
	}
	productionService.randFloat = func() float64 { return 0 }
	job, afterStart, err := productionService.Start(ctx, player.ID("p1"), "clay-1", "clay_quarry_run")
	if err != nil {
		t.Fatal(err)
	}
	if afterStart.Items[economy.ResourceFuel] != 0 || afterStart.Items[economy.ResourcePopulation] != inventory.Items[economy.ResourcePopulation]-13 || job.CompletesAt.Sub(job.StartedAt) != 1410*time.Second {
		t.Fatalf("unexpected quarry costs or duration: %#v %#v", afterStart.Items, job)
	}
	if _, err := productionService.ReadyAt(ctx, player.ID("p1"), job.ID, job.CompletesAt); err != nil {
		t.Fatal(err)
	}
	_, afterCollect, err := productionService.CompleteAt(ctx, player.ID("p1"), job.ID, job.CompletesAt)
	if err != nil {
		t.Fatal(err)
	}
	if afterCollect.Items[economy.ResourceClay] != inventory.Items[economy.ResourceClay]+150 || afterCollect.Items[economy.ResourceKaolin] != inventory.Items[economy.ResourceKaolin]+1 || afterCollect.Items[economy.ResourcePopulation] != inventory.Items[economy.ResourcePopulation] {
		t.Fatalf("unexpected clay quarry output: %#v", afterCollect.Items)
	}
}

func TestProductionRecipesExposeEveryClayQuarryLevel(t *testing.T) {
	_, _, _, productionService := newProductionPopulationTestServices()
	recipes, err := productionService.Recipes(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	levels := make(map[int]bool)
	for _, recipe := range recipes {
		if recipe.BuildingType == "clay_quarry" {
			levels[recipe.RequiredLevel] = true
		}
	}
	if len(levels) != 12 {
		t.Fatalf("expected all 12 clay quarry levels, got %#v", levels)
	}
}

func TestProductionRecipesExposeEveryLumberYardLevel(t *testing.T) {
	_, _, _, productionService := newProductionPopulationTestServices()
	recipes, err := productionService.Recipes(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	levels := make(map[int]bool)
	for _, recipe := range recipes {
		if recipe.BuildingType == "lumber_yard" {
			levels[recipe.RequiredLevel] = true
		}
	}
	if len(levels) != 13 {
		t.Fatalf("expected all 13 sawmill levels, got %#v", levels)
	}
}

func TestBuildingCannotChangeWhileProductionWorkersOrRewardsArePending(t *testing.T) {
	ctx := context.Background()
	buildingRepo, economyRepo, economyService, productionService := newProductionPopulationTestServices()
	buildingService := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	buildingService.SetEconomy(economyService)
	createActiveProductionBuilding(t, ctx, buildingRepo, "lumber-1", player.ID("p1"), building.TypeLumberYard, 1)
	start := setTestPopulation(t, ctx, economyRepo, economyService, player.ID("p1"), 10)
	job, _, err := productionService.Start(ctx, player.ID("p1"), "lumber-1", "planks_from_wood")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := buildingService.Upgrade(ctx, building.ID("lumber-1"), player.ID("p1")); err == nil {
		t.Fatal("expected upgrade during production to be rejected")
	}
	if _, err := productionService.ReadyAt(ctx, player.ID("p1"), job.ID, job.CompletesAt.Add(time.Second)); err != nil {
		t.Fatal(err)
	}
	if _, err := buildingService.Upgrade(ctx, building.ID("lumber-1"), player.ID("p1")); err == nil {
		t.Fatal("expected upgrade before collecting production rewards to be rejected")
	}
	if _, _, err := productionService.CompleteAt(ctx, player.ID("p1"), job.ID, job.CompletesAt.Add(time.Second)); err != nil {
		t.Fatal(err)
	}
	if err := buildingService.Demolish(ctx, building.ID("lumber-1"), player.ID("p1")); err != nil {
		t.Fatal(err)
	}
	inventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if inventory.Items[economy.ResourcePopulation] != start.Items[economy.ResourcePopulation] {
		t.Fatalf("expected workers to return after production, got %d", inventory.Items[economy.ResourcePopulation])
	}
}

func TestReleasingProductionWorkersDoesNotTriggerNestedCatchUp(t *testing.T) {
	ctx := context.Background()
	buildingRepo, economyRepo, economyService, productionService := newProductionPopulationTestServices()
	createActiveProductionBuilding(t, ctx, buildingRepo, "lumber-1", player.ID("p1"), building.TypeLumberYard, 1)
	start := setTestPopulation(t, ctx, economyRepo, economyService, player.ID("p1"), 10)
	job, _, err := productionService.Start(ctx, player.ID("p1"), "lumber-1", "planks_from_wood")
	if err != nil {
		t.Fatal(err)
	}
	catchUpCalls := 0
	economyService.SetCatchUp(func(ctx context.Context, playerID player.ID) error {
		catchUpCalls++
		_, err := productionService.ReadyAt(ctx, playerID, job.ID, job.CompletesAt.Add(time.Second))
		return err
	})
	inventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if catchUpCalls != 1 || inventory.Items[economy.ResourcePopulation] != start.Items[economy.ResourcePopulation] {
		t.Fatalf("expected one catch-up and returned workers, got calls=%d population=%d", catchUpCalls, inventory.Items[economy.ResourcePopulation])
	}
}

func TestProductionServiceRejectsStartWhenPopulationIsBusy(t *testing.T) {
	ctx := context.Background()
	buildingRepo, economyRepo, economyService, productionService := newProductionPopulationTestServices()
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	economyService.now = func() time.Time { return now }
	productionService.now = func() time.Time { return now }
	createActiveProductionBuilding(t, ctx, buildingRepo, "lumber-1", player.ID("p1"), building.TypeLumberYard, 1)

	startInventory := setTestPopulation(t, ctx, economyRepo, economyService, player.ID("p1"), 2)
	if _, _, err := productionService.Start(ctx, player.ID("p1"), "lumber-1", "planks_from_wood"); err == nil {
		t.Fatal("expected production start to fail without enough free population")
	}
	inventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if inventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation] {
		t.Fatalf("population should stay unchanged after rejected start, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], inventory.Items[economy.ResourcePopulation])
	}
	jobs, err := economyRepo.ListProductionJobs(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if len(jobs) != 0 {
		t.Fatalf("expected no production job to be created, got %#v", jobs)
	}
}

func TestProductionServiceReleasesPopulationOnDirectCompleteAndCancel(t *testing.T) {
	ctx := context.Background()
	buildingRepo, economyRepo, economyService, productionService := newProductionPopulationTestServices()
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	economyService.now = func() time.Time { return now }
	productionService.now = func() time.Time { return now }
	createActiveProductionBuilding(t, ctx, buildingRepo, "lumber-1", player.ID("p1"), building.TypeLumberYard, 1)
	createActiveProductionBuilding(t, ctx, buildingRepo, "lumber-2", player.ID("p1"), building.TypeLumberYard, 1)

	startInventory := setTestPopulation(t, ctx, economyRepo, economyService, player.ID("p1"), 10)
	cancelledJob, _, err := productionService.Start(ctx, player.ID("p1"), "lumber-1", "planks_from_wood")
	if err != nil {
		t.Fatalf("start cancelled production: %v", err)
	}
	if _, err := productionService.Cancel(ctx, player.ID("p1"), cancelledJob.ID); err != nil {
		t.Fatalf("cancel production: %v", err)
	}
	afterCancel, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if afterCancel.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation] {
		t.Fatalf("expected workers released after cancel, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], afterCancel.Items[economy.ResourcePopulation])
	}

	completedJob, _, err := productionService.Start(ctx, player.ID("p1"), "lumber-2", "planks_from_wood")
	if err != nil {
		t.Fatalf("start completed production: %v", err)
	}
	now = completedJob.CompletesAt.Add(time.Second)
	if _, _, err := productionService.CompleteAt(ctx, player.ID("p1"), completedJob.ID, now); err != nil {
		t.Fatalf("complete production: %v", err)
	}
	afterComplete, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if afterComplete.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation] {
		t.Fatalf("expected workers released after direct complete, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], afterComplete.Items[economy.ResourcePopulation])
	}
}

func newProductionPopulationTestServices() (*memory.BuildingRepo, *memory.EconomyRepo, *EconomyService, *ProductionService) {
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	economyService := NewEconomyService(economyRepo, buildingRepo, log)
	productionService := NewProductionService(economyRepo, economyService, log)
	productionService.SetBuildings(buildingRepo)
	return buildingRepo, economyRepo, economyService, productionService
}

func createActiveProductionBuilding(t *testing.T, ctx context.Context, repo *memory.BuildingRepo, id building.ID, owner player.ID, kind building.Type, level int) {
	t.Helper()
	now := time.Date(2026, 8, 25, 9, 0, 0, 0, time.UTC)
	if err := repo.Create(ctx, building.Building{
		ID:        id,
		MapID:     DefaultWorldID,
		OwnerID:   string(owner),
		Type:      kind,
		Name:      string(kind),
		Level:     level,
		State:     building.StateActive,
		Health:    100,
		Tile:      world.Coord{X: len(id), Y: len(id)},
		Footprint: building.Footprint{Width: 1, Height: 1},
		StartedAt: now,
		CreatedAt: now,
		UpdatedAt: now,
	}); err != nil {
		t.Fatalf("create active building: %v", err)
	}
}

func setTestPopulation(t *testing.T, ctx context.Context, repo *memory.EconomyRepo, service *EconomyService, playerID player.ID, population int) economy.Inventory {
	t.Helper()
	inventory, err := service.Inventory(ctx, playerID)
	if err != nil {
		t.Fatal(err)
	}
	inventory.Items[economy.ResourcePopulation] = population
	inventory.Items[economy.ResourceWood] = 100
	if err := repo.SaveInventory(ctx, inventory); err != nil {
		t.Fatal(err)
	}
	return inventory
}
