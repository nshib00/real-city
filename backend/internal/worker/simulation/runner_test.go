package simulation

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
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

func TestRunnerCompletesQueuedBuildingAction(t *testing.T) {
	ctx := context.Background()
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	worldRepo := memory.NewWorldRepo()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	actionRepo := memory.NewActionRepo()
	events := service.NewEventBus(2)
	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	buildings := service.NewBuildingService(buildingRepo, worldRepo, log)
	buildings.SetEconomy(economyService)
	buildings.SetActionQueue(actionRepo)
	buildings.SetEventBus(events)

	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	buildingsNow := now
	buildings.SetNowForTest(func() time.Time { return buildingsNow })
	if _, err := buildings.Place(ctx, service.PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeTownHall, Tile: world.Coord{X: 0, Y: 0}}); err != nil {
		t.Fatalf("place town hall: %v", err)
	}
	dugout, err := buildings.Place(ctx, service.PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeDugout, Tile: world.Coord{X: 4, Y: 4}})
	if err != nil {
		t.Fatalf("place dugout: %v", err)
	}
	if dugout.CompletesAt == nil {
		t.Fatal("expected scheduled construction")
	}

	runner := NewRunner(actionRepo, nil, buildings, nil, nil, log, config.SimulationConfig{BatchSize: 10, LockTTL: time.Second, TickInterval: time.Second})
	runner.now = func() time.Time { return dugout.CompletesAt.Add(time.Second) }
	result, err := runner.Tick(ctx)
	if err != nil {
		t.Fatalf("tick: %v", err)
	}
	if result.ActionsProcessed != 1 {
		t.Fatalf("actions processed = %d", result.ActionsProcessed)
	}
	updated, err := buildingRepo.FindByID(ctx, dugout.ID)
	if err != nil {
		t.Fatalf("find building: %v", err)
	}
	if updated.State != building.StateActive || updated.CompletesAt != nil {
		t.Fatalf("building was not completed: %#v", updated)
	}
}

func TestRunnerCompletesDueProduction(t *testing.T) {
	ctx := context.Background()
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	production := service.NewProductionService(economyRepo, economyService, log)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	job := economy.ProductionJob{
		ID:          "job_due",
		PlayerID:    "p1",
		BuildingID:  "b1",
		RecipeID:    "planks_from_wood",
		State:       economy.ProductionRunning,
		StartedAt:   now.Add(-time.Minute),
		CompletesAt: now,
		CreatedAt:   now.Add(-time.Minute),
		UpdatedAt:   now.Add(-time.Minute),
	}
	if err := economyRepo.SaveProductionJob(ctx, job); err != nil {
		t.Fatalf("save job: %v", err)
	}

	runner := NewRunner(nil, nil, nil, production, nil, log, config.SimulationConfig{BatchSize: 10, LockTTL: time.Second, TickInterval: time.Second})
	runner.now = func() time.Time { return now.Add(time.Second) }
	result, err := runner.Tick(ctx)
	if err != nil {
		t.Fatalf("tick: %v", err)
	}
	if result.ProductionCompleted != 1 {
		t.Fatalf("production completed = %d", result.ProductionCompleted)
	}
	updated, err := economyRepo.FindProductionJob(ctx, job.ID)
	if err != nil {
		t.Fatalf("find job: %v", err)
	}
	if updated.State != economy.ProductionCompleted {
		t.Fatalf("job was not completed: %#v", updated)
	}
}
