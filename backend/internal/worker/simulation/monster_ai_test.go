package simulation

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
)

func TestMonsterAITickAggrosNearestBuilding(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsterRepo := memory.NewMonsterRepo()
	buildingRepo := memory.NewBuildingRepo()
	spec, _ := catalog.MonsterSpec(monster.TypeRoamingMelee)
	item := monster.Monster{
		ID: "test_monster", MapID: "dev-world", Type: spec.Type, State: monster.StateWandering,
		Tile: world.Coord{X: 1, Y: 1}, HomeTile: world.Coord{X: 1, Y: 1}, Health: spec.MaxHealth, MaxHealth: spec.MaxHealth,
		Damage: spec.Damage, SpeedTiles: spec.SpeedTiles, AggroRadius: spec.AggroRadius, AttackRange: spec.AttackRange,
		AttackCooldown: spec.AttackCooldown, LastMovedAt: now, CreatedAt: now, UpdatedAt: now,
	}
	if err := monsterRepo.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if err := buildingRepo.Create(ctx, building.Building{
		ID: "target", MapID: "dev-world", OwnerID: "p1", Type: building.TypeTownHall, State: building.StateActive,
		Tile: world.Coord{X: 3, Y: 1}, Health: 100, CreatedAt: now, UpdatedAt: now,
	}); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(monsterRepo, buildingRepo, nil, nil, slog.Default())
	processed, err := ai.Tick(ctx, now.Add(time.Second), 10)
	if err != nil {
		t.Fatal(err)
	}
	if processed == 0 {
		t.Fatal("expected processed monsters")
	}
	updated, err := monsterRepo.FindByID(ctx, item.ID)
	if err != nil {
		t.Fatal(err)
	}
	if updated.State != monster.StateAggro {
		t.Fatalf("expected aggro state, got %s", updated.State)
	}
	if updated.Tile != (world.Coord{X: 2, Y: 1}) {
		t.Fatalf("expected movement toward target, got %+v", updated.Tile)
	}
}
