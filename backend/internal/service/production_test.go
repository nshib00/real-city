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
