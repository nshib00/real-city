package memory

import (
	"context"
	"sync"

	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

type WorldRepo struct {
	mu        sync.RWMutex
	generator worldgen.Generator
	maps      map[string]world.WorldMap
	chunks    map[string]world.Chunk
}

const (
	devWorldMapID       = "dev-world"
	devWorldSeed        = 20260727
	devWorldSpawnRadius = 10
)

func NewWorldRepo() *WorldRepo {
	generator := worldgen.New(devWorldMapID, devWorldSeed, devWorldSpawnRadius)
	worldMap := generator.Map()
	return &WorldRepo{
		generator: generator,
		maps:      map[string]world.WorldMap{worldMap.ID: worldMap},
		chunks:    make(map[string]world.Chunk),
	}
}

func (r *WorldRepo) GetMap(ctx context.Context, id string) (world.WorldMap, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	worldMap, ok := r.maps[id]
	if !ok {
		return world.WorldMap{}, apperror.New(apperror.NotFound, "world map not found")
	}
	return worldMap, nil
}

func (r *WorldRepo) GetOrCreateChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (world.Chunk, bool, error) {
	coord = world.NormalizeChunk(coord)
	_ = ctx
	key := world.ChunkID(mapID, coord)
	r.mu.RLock()
	chunk, ok := r.chunks[key]
	r.mu.RUnlock()
	if ok {
		return chunk, true, nil
	}

	r.mu.Lock()
	defer r.mu.Unlock()
	if chunk, ok = r.chunks[key]; ok {
		return chunk, true, nil
	}
	if _, ok := r.maps[mapID]; !ok {
		return world.Chunk{}, false, apperror.New(apperror.NotFound, "world map not found")
	}
	chunk = r.generator.Chunk(coord)
	r.chunks[key] = chunk
	return chunk, false, nil
}

func (r *WorldRepo) GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	coords = world.UniqueChunks(coords)
	chunks := make([]world.Chunk, 0, len(coords))
	for _, coord := range coords {
		chunk, _, err := r.GetOrCreateChunk(ctx, mapID, coord)
		if err != nil {
			return nil, err
		}
		chunks = append(chunks, chunk)
	}
	return chunks, nil
}

func (r *WorldRepo) GetOrCreateChunksFresh(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	coords = world.UniqueChunks(coords)
	return r.GetOrCreateChunks(ctx, mapID, coords)
}

func (r *WorldRepo) UpdateTile(ctx context.Context, tile world.Tile) error {
	tile.Coord = world.NormalizeCoord(tile.Coord)
	tile.Chunk = world.ChunkForTile(tile.Coord)
	_ = ctx
	key := world.ChunkID(tile.MapID, tile.Chunk)
	r.mu.Lock()
	defer r.mu.Unlock()
	chunk, ok := r.chunks[key]
	if !ok {
		return apperror.New(apperror.NotFound, "world chunk not found")
	}
	for i := range chunk.Tiles {
		if chunk.Tiles[i].Coord == tile.Coord {
			chunk.Tiles[i] = tile
			chunk.Version++
			r.chunks[key] = chunk
			return nil
		}
	}
	return apperror.New(apperror.NotFound, "world tile not found")
}
