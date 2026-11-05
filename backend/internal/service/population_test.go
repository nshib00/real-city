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
)

func TestPopulationSummaryTracksReservedWorkers(t *testing.T) {
	ctx := context.Background()
	playerID := player.ID("p1")
	now := time.Date(2026, 10, 16, 10, 0, 0, 0, time.UTC)
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	economyService.now = func() time.Time { return now }
	inventory, err := economyService.Inventory(ctx, playerID)
	if err != nil {
		t.Fatal(err)
	}
	inventory.Items[economy.ResourcePopulation] = 10
	if err := economyRepo.SaveInventory(ctx, inventory); err != nil {
		t.Fatal(err)
	}
	readyAt := now.Add(time.Minute)
	for _, item := range []building.Building{
		{ID: "dugout", MapID: DefaultWorldID, OwnerID: string(playerID), Type: building.TypeDugout, Level: 1, State: building.StateBuilding, CompletesAt: &readyAt},
		{ID: "field", MapID: DefaultWorldID, OwnerID: string(playerID), Type: building.TypeFieldBed, Level: 1, State: building.StateActive, FieldStage: 1, FieldStageStartedAt: &now, FieldStageReadyAt: &readyAt},
		{ID: "lumber", MapID: DefaultWorldID, OwnerID: string(playerID), Type: building.TypeLumberYard, Level: 1, State: building.StateActive},
	} {
		if err := buildingRepo.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	if err := economyRepo.SaveProductionJob(ctx, economy.ProductionJob{ID: "job", PlayerID: string(playerID), BuildingID: "lumber", RecipeID: "planks_from_wood", State: economy.ProductionRunning, CompletesAt: readyAt}); err != nil {
		t.Fatal(err)
	}
	if _, err := economyService.Spend(ctx, playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: 5}}, "test:workers"); err != nil {
		t.Fatal(err)
	}
	summary, err := NewPopulationService(economyService).Summary(ctx, playerID)
	if err != nil {
		t.Fatal(err)
	}
	if summary.Total != 10 || summary.Free != 5 || summary.Builders != 1 || summary.Fields != 1 || summary.Production != 3 {
		t.Fatalf("unexpected population summary: %#v", summary)
	}
}

func TestPopulationSummaryKeepsTotalWhenDefenseStaffChanges(t *testing.T) {
	ctx := context.Background()
	owner := player.ID("owner")
	buildings := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	eco := NewEconomyService(economyRepo, buildings, slog.Default())
	svc := NewBuildingService(buildings, memory.NewWorldRepo(), slog.Default())
	svc.SetEconomy(eco)
	for _, item := range []building.Building{
		{ID: "tower", OwnerID: string(owner), Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100},
		{ID: "cannon", OwnerID: string(owner), Type: building.TypeDefenseCannon, Level: 1, State: building.StateActive, Health: 100},
	} {
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	stock, err := eco.Inventory(ctx, owner)
	if err != nil {
		t.Fatal(err)
	}
	stock.Items[economy.ResourcePopulation] = 3
	if err := economyRepo.SaveInventory(ctx, stock); err != nil {
		t.Fatal(err)
	}
	assertSummary := func(wantFree, wantDefense int) {
		t.Helper()
		summary, err := NewPopulationService(eco).Summary(ctx, owner)
		if err != nil {
			t.Fatal(err)
		}
		if summary.Total != 3 || summary.Free != wantFree || summary.Defense != wantDefense {
			t.Fatalf("population = %+v, want total=3 free=%d defense=%d", summary, wantFree, wantDefense)
		}
	}
	assertSummary(3, 0)
	if _, err := svc.SetCannonEnabled(ctx, "cannon", owner, true); err != nil {
		t.Fatal(err)
	}
	assertSummary(2, 1)
	if _, err := svc.SetTowerWatchkeeper(ctx, "tower", owner, true); err != nil {
		t.Fatal(err)
	}
	assertSummary(1, 2)
	if _, err := svc.SetTowerWatchkeeper(ctx, "tower", owner, false); err != nil {
		t.Fatal(err)
	}
	assertSummary(2, 1)
	if _, err := svc.SetCannonEnabled(ctx, "cannon", owner, false); err != nil {
		t.Fatal(err)
	}
	assertSummary(3, 0)
}
