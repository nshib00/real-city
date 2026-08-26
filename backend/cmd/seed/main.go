package main

import (
	"encoding/json"
	"fmt"
	"os"

	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
)

type summary struct {
	MapID      string         `json:"map_id"`
	ChunkSize  int            `json:"chunk_size"`
	ChunkCount int            `json:"chunk_count"`
	TileCount  int            `json:"tile_count"`
	Terrain    map[string]int `json:"terrain"`
}

func main() {
	generator := worldgen.New("dev-world", 20260727, 10)
	chunks := world.ChunksAround(world.ChunkCoord{}, 1)
	result := summary{
		MapID:      generator.Map().ID,
		ChunkSize:  world.ChunkSize,
		ChunkCount: len(chunks),
		Terrain:    make(map[string]int),
	}
	for _, coord := range chunks {
		chunk := generator.Chunk(coord)
		result.TileCount += len(chunk.Tiles)
		for _, tile := range chunk.Tiles {
			result.Terrain[string(tile.Terrain)]++
		}
	}
	if err := json.NewEncoder(os.Stdout).Encode(result); err != nil {
		_, _ = fmt.Fprintf(os.Stderr, "seed summary failed: %v\n", err)
		os.Exit(1)
	}
}
