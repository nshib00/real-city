package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/world"
)

type testWorldCache struct{ values map[string][]byte }

func (c *testWorldCache) Get(_ context.Context, key string) ([]byte, bool, error) {
	v, ok := c.values[key]
	return v, ok, nil
}
func (c *testWorldCache) Set(_ context.Context, key string, value []byte, _ time.Duration) error {
	c.values[key] = value
	return nil
}
func (c *testWorldCache) Delete(_ context.Context, key string) error {
	delete(c.values, key)
	return nil
}

func TestWorldChunkCacheInvalidatesOnMapEvent(t *testing.T) {
	service := NewWorldService(memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	cache := &testWorldCache{values: map[string][]byte{}}
	service.SetCache(cache)
	coord := world.ChunkCoord{X: 0, Y: 0}
	if _, err := service.GetChunk(context.Background(), coord); err != nil {
		t.Fatal(err)
	}
	key := chunkCacheKey(DefaultWorldID, coord)
	if _, ok := cache.values[key]; !ok {
		t.Fatal("chunk was not cached")
	}
	service.InvalidateEvent(context.Background(), Event{Type: EventBuildingUpdated, ChunkID: world.ChunkID(DefaultWorldID, coord)})
	if _, ok := cache.values[key]; ok {
		t.Fatal("chunk remained cached after map update")
	}
}

func TestWorldServiceLoadsVisibleChunks(t *testing.T) {
	service := NewWorldService(memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	chunks, err := service.ListChunks(context.Background(), world.ChunkCoord{X: 0, Y: 0}, 1)
	if err != nil {
		t.Fatalf("ListChunks error: %v", err)
	}
	if len(chunks) != 9 {
		t.Fatalf("chunks len = %d", len(chunks))
	}
	if len(chunks[0].Tiles) != world.ChunkSize*world.ChunkSize {
		t.Fatalf("chunk tiles len = %d", len(chunks[0].Tiles))
	}
}

func TestWorldServiceLoadsCanonicalChunksAcrossWorldEdge(t *testing.T) {
	service := NewWorldService(memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	chunks, err := service.ListChunks(context.Background(), world.ChunkCoord{X: 0, Y: 0}, 1)
	if err != nil {
		t.Fatal(err)
	}
	seen := make(map[world.ChunkCoord]bool)
	for _, chunk := range chunks {
		if chunk.Coord.X < 0 || chunk.Coord.X >= 5 || chunk.Coord.Y < 0 || chunk.Coord.Y >= 5 {
			t.Fatalf("noncanonical chunk: %#v", chunk.Coord)
		}
		if seen[chunk.Coord] {
			t.Fatalf("duplicate chunk: %#v", chunk.Coord)
		}
		seen[chunk.Coord] = true
	}
	for _, coord := range []world.ChunkCoord{{X: 4, Y: 0}, {X: 0, Y: 0}, {X: 0, Y: 4}, {X: 4, Y: 4}} {
		if !seen[coord] {
			t.Fatalf("missing edge chunk: %#v", coord)
		}
	}
	if got := visibleWorldChunks(world.ChunkCoord{X: 4, Y: 4}, 3); len(got) != 25 {
		t.Fatalf("wide viewport returned %d chunks, want 25", len(got))
	}
}

func TestWorldServiceRejectsOversizedRadius(t *testing.T) {
	service := NewWorldService(memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	if _, err := service.ListChunks(context.Background(), world.ChunkCoord{}, MaxChunkRadius+1); err == nil {
		t.Fatal("expected oversized radius error")
	}
}
