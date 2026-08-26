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

func TestWorldServiceRejectsOversizedRadius(t *testing.T) {
	service := NewWorldService(memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	if _, err := service.ListChunks(context.Background(), world.ChunkCoord{}, MaxChunkRadius+1); err == nil {
		t.Fatal("expected oversized radius error")
	}
}
