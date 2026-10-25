package service

import (
	"context"
	"io"
	"log/slog"
	"testing"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/world"
)

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
