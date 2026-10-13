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

func TestFieldServiceManualWindleafCycleReservesAndReleasesPopulation(t *testing.T) {
	ctx := context.Background()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	buildingService := NewBuildingService(buildingRepo, memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	buildingService.SetEconomy(economyService)
	fieldService := NewFieldService(economyService, buildingRepo)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	buildingService.now = func() time.Time { return now }
	economyService.now = func() time.Time { return now }
	fieldService.SetNowForTest(func() time.Time { return now })
	fieldService.SetSuperRollForTest(func(chanceBps int) bool { return false })

	if _, err := buildingService.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	grantTestResources(t, ctx, economyService, player.ID("p1"),
		economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: 250},
		economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 4},
		economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 2},
	)
	bed, err := buildingService.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeFieldBed, Tile: world.Coord{X: 4, Y: 4}})
	if err != nil {
		t.Fatalf("place windleaf bed: %v", err)
	}
	now = bed.CompletesAt.Add(time.Second)
	completed, err := buildingService.Complete(ctx, bed.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("complete windleaf bed: %v", err)
	}
	startInventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatal(err)
	}
	if completed.FieldStage != 0 {
		t.Fatalf("expected idle completed field, got stage %d", completed.FieldStage)
	}

	started, inventory, err := fieldService.AdvanceWindleaf(ctx, player.ID("p1"), bed.ID)
	if err != nil {
		t.Fatalf("start windleaf cycle: %v", err)
	}
	if started.FieldStage != 1 || started.FieldStageStartedAt == nil || started.FieldStageReadyAt == nil {
		t.Fatalf("expected first field stage after manual start, got %#v", started)
	}
	if inventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation]-1 {
		t.Fatalf("expected one field worker reserved, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], inventory.Items[economy.ResourcePopulation])
	}

	for stage := 2; stage <= 4; stage++ {
		now = started.FieldStageReadyAt.Add(time.Second)
		readyInventory, err := economyService.Inventory(ctx, player.ID("p1"))
		if err != nil {
			t.Fatalf("inventory after field stage %d completed: %v", stage-1, err)
		}
		if readyInventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation] {
			t.Fatalf("expected field worker released after stage %d completed, got start=%d after=%d", stage-1, startInventory.Items[economy.ResourcePopulation], readyInventory.Items[economy.ResourcePopulation])
		}
		started, inventory, err = fieldService.AdvanceWindleaf(ctx, player.ID("p1"), bed.ID)
		if err != nil {
			t.Fatalf("advance windleaf stage %d: %v", stage, err)
		}
		if started.FieldStage != stage {
			t.Fatalf("expected stage %d, got %#v", stage, started)
		}
		if inventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation]-1 {
			t.Fatalf("expected stage %d to reserve one field worker, got start=%d after=%d", stage, startInventory.Items[economy.ResourcePopulation], inventory.Items[economy.ResourcePopulation])
		}
	}

	now = started.FieldStageReadyAt.Add(time.Second)
	readyInventory, err := economyService.Inventory(ctx, player.ID("p1"))
	if err != nil {
		t.Fatalf("inventory after final field stage completed: %v", err)
	}
	if readyInventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation] {
		t.Fatalf("expected field worker released after final stage, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], readyInventory.Items[economy.ResourcePopulation])
	}
	harvested, inventory, err := fieldService.HarvestWindleaf(ctx, player.ID("p1"), bed.ID)
	if err != nil {
		t.Fatalf("harvest windleaf: %v", err)
	}
	if harvested.FieldStage != 0 || harvested.FieldStageStartedAt != nil || harvested.FieldStageReadyAt != nil {
		t.Fatalf("expected idle field after harvest, got %#v", harvested)
	}
	if inventory.Items[economy.ResourcePopulation] != startInventory.Items[economy.ResourcePopulation] {
		t.Fatalf("expected field worker released, got start=%d after=%d", startInventory.Items[economy.ResourcePopulation], inventory.Items[economy.ResourcePopulation])
	}
}
