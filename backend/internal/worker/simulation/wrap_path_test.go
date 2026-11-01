package simulation

import (
	"context"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"testing"
)

func TestMonsterPathCrossesWorldSeam(t *testing.T) {
	ctx := context.Background()
	worlds := memory.NewWorldRepo()
	from, to := world.Coord{X: 159, Y: 4}, world.Coord{X: 0, Y: 4}
	for _, tile := range []world.Coord{from, to} {
		if _, _, err := worlds.GetOrCreateChunk(ctx, service.DefaultWorldID, world.ChunkForTile(tile)); err != nil {
			t.Fatal(err)
		}
		if err := worlds.UpdateTile(ctx, world.Tile{MapID: service.DefaultWorldID, Coord: tile, Chunk: world.ChunkForTile(tile), Terrain: world.TerrainGrass}); err != nil {
			t.Fatal(err)
		}
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), memory.NewBuildingRepo(), worlds, nil, slog.Default())
	path, err := ai.nextPassablePath(ctx, from, to, 1, 0, map[world.ChunkCoord]world.Chunk{})
	if err != nil || len(path) != 1 || path[0] != to {
		t.Fatalf("path=%v error=%v", path, err)
	}
}
