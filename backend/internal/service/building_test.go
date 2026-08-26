package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
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
