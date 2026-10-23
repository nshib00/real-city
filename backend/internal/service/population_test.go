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
