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

func TestCreatedMonsterIgnoresCreatorAndExpires(t *testing.T) {
	ctx, now := context.Background(), time.Now().UTC()
	monsters, buildings := memory.NewMonsterRepo(), memory.NewBuildingRepo()
	for _, b := range []building.Building{
		{ID: "own", OwnerID: "creator", MapID: service.DefaultWorldID, Tile: world.Coord{X: 5, Y: 5}, State: building.StateActive, Health: 100, Footprint: building.Footprint{Width: 1, Height: 1}},
		{ID: "enemy", OwnerID: "enemy", MapID: service.DefaultWorldID, Tile: world.Coord{X: 7, Y: 5}, State: building.StateActive, Health: 100, Footprint: building.Footprint{Width: 1, Height: 1}},
	} {
		if err := buildings.Create(ctx, b); err != nil {
			t.Fatal(err)
		}
	}
	ai := NewMonsterAI(monsters, buildings, nil, nil, slog.Default())
	item := monster.Monster{ID: "created", MapID: service.DefaultWorldID, CreatorID: "creator", ExpiresAt: now.Add(time.Minute), Tile: world.Coord{X: 5, Y: 5}, State: monster.StateAggro, Health: 100, AggroRadius: 8, SpeedTiles: 1, AttackRange: 1}
	target, ok, err := ai.nearestTarget(ctx, item)
	if err != nil || !ok || target.ID != "enemy" {
		t.Fatalf("target=%+v ok=%v err=%v", target, ok, err)
	}
	updated, event, _, _, err := ai.step(ctx, item, now.Add(2*time.Minute), map[world.ChunkCoord]world.Chunk{})
	if err != nil || updated.Alive() || event != service.EventMonsterDespawned {
		t.Fatalf("expiry=%+v event=%s err=%v", updated, event, err)
	}
}
