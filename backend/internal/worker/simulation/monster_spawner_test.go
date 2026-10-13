package simulation

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

func TestMonsterSpawnerRelocatesUnsafeSpawnAndCreatesMonster(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, 10, 12, 12, 0, 0, 0, time.UTC)
	monsterRepo := memory.NewMonsterRepo()
	buildingRepo := memory.NewBuildingRepo()

	source, err := monsterRepo.FindByID(ctx, "monster_roamer_1")
	if err != nil {
		t.Fatal(err)
	}
	source.State = monster.StateDead
	source.Health = 0
	if err := monsterRepo.Update(ctx, source); err != nil {
		t.Fatal(err)
	}
	spawn := monster.SpawnPoint{
		ID:          "spawn_roamers",
		MapID:       service.DefaultWorldID,
		Type:        monster.TypeRoamingMelee,
		Tile:        world.Coord{X: 6, Y: -7},
		Radius:      8,
		MaxAlive:    1,
		Cooldown:    90 * time.Second,
		NextSpawnAt: now.Add(-time.Second),
		CreatedAt:   now.Add(-time.Hour),
		UpdatedAt:   now.Add(-time.Hour),
	}
	if err := monsterRepo.SaveSpawnPoint(ctx, spawn); err != nil {
		t.Fatal(err)
	}
	if err := buildingRepo.Create(ctx, building.Building{
		ID:        "blocking_building",
		MapID:     service.DefaultWorldID,
		OwnerID:   "p1",
		Type:      building.TypeTownHall,
		State:     building.StateActive,
		Tile:      spawn.Tile,
		Footprint: building.Footprint{Width: 1, Height: 1},
		Health:    100,
		CreatedAt: now,
		UpdatedAt: now,
	}); err != nil {
		t.Fatal(err)
	}

	monsterService := service.NewMonsterService(monsterRepo, slog.Default())
	spawner := NewMonsterSpawner(monsterService, monsterRepo, buildingRepo, nil, slog.Default())
	spawned, err := spawner.Tick(ctx, now, 10)
	if err != nil {
		t.Fatalf("tick spawner: %v", err)
	}
	if spawned != 1 {
		t.Fatalf("expected one spawned monster, got %d", spawned)
	}
	spawns, err := monsterRepo.ListSpawnPoints(ctx, service.DefaultWorldID)
	if err != nil {
		t.Fatal(err)
	}
	for _, updated := range spawns {
		if updated.ID != spawn.ID {
			continue
		}
		if manhattan(updated.Tile, spawn.Tile) < monsterSpawnSafeRange {
			t.Fatalf("spawn point was not relocated far enough: %+v", updated.Tile)
		}
		if updated.NextSpawnAt.Sub(now) < time.Minute || updated.NextSpawnAt.Sub(now) > 2*time.Minute {
			t.Fatalf("unexpected next spawn delay: %s", updated.NextSpawnAt.Sub(now))
		}
		return
	}
	t.Fatal("spawn point was not found")
}
