package service

import (
	"context"
	"io"
	"log/slog"
	"testing"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/world"
)

func TestViewportWrapsAcrossBothWorldSeams(t *testing.T) {
	service := NewWorldService(memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	for _, center := range []world.Coord{{X: 0, Y: 0}, {X: world.WorldSize - 1, Y: world.WorldSize - 1}, {X: -1, Y: world.WorldSize}} {
		chunks, err := service.LoadViewport(context.Background(), world.Viewport{Center: center, Radius: 32})
		if err != nil {
			t.Fatal(err)
		}
		seen := make(map[world.ChunkCoord]bool, len(chunks))
		for _, chunk := range chunks {
			seen[chunk.Coord] = true
		}
		if len(chunks) != 9 || len(seen) != 9 {
			t.Fatalf("center=%+v returned %d chunks, %d unique", center, len(chunks), len(seen))
		}
		for _, corner := range []world.ChunkCoord{{X: 0, Y: 0}, {X: 0, Y: world.WorldChunks - 1}, {X: world.WorldChunks - 1, Y: 0}, {X: world.WorldChunks - 1, Y: world.WorldChunks - 1}} {
			if !seen[corner] {
				t.Fatalf("center=%+v missing seam chunk %+v", center, corner)
			}
		}
	}
}
