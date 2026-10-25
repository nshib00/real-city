package service

import (
	"context"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

const (
	DefaultWorldID     = "dev-world"
	MaxChunkRadius     = 3
	MaxViewportRadius  = 96
	DefaultChunkRadius = 1
)

type WorldService struct {
	repo WorldRepository
	log  *slog.Logger
}

func NewWorldService(repo WorldRepository, log *slog.Logger) *WorldService {
	return &WorldService{repo: repo, log: log}
}

func (s *WorldService) GetWorld(ctx context.Context) (world.WorldMap, error) {
	return s.repo.GetMap(ctx, DefaultWorldID)
}

func (s *WorldService) GetChunk(ctx context.Context, coord world.ChunkCoord) (world.Chunk, error) {
	start := time.Now()
	chunk, hit, err := s.repo.GetOrCreateChunk(ctx, DefaultWorldID, coord)
	s.log.Info("world.chunk.loaded",
		"event", "world.chunk.loaded",
		"map_id", DefaultWorldID,
		"chunk_id", world.ChunkID(DefaultWorldID, coord),
		"chunk_x", coord.X,
		"chunk_y", coord.Y,
		"cache_hit", hit,
		"duration_ms", time.Since(start).Milliseconds(),
	)
	return chunk, err
}

func (s *WorldService) ListChunks(ctx context.Context, center world.ChunkCoord, radius int) ([]world.Chunk, error) {
	if radius < 0 {
		return nil, apperror.WithFields(apperror.Validation, "radius must be non-negative", map[string]string{"radius": "must be >= 0"})
	}
	if radius > MaxChunkRadius {
		s.log.Warn("world.chunk.radius_oversized",
			"event", "world.chunk.radius_oversized",
			"requested_radius", radius,
			"max_radius", MaxChunkRadius,
		)
		return nil, apperror.WithFields(apperror.Validation, "radius is too large", map[string]string{"radius": "must be <= 3"})
	}
	start := time.Now()
	coords := visibleWorldChunks(center, radius)
	chunks, err := s.repo.GetOrCreateChunks(ctx, DefaultWorldID, coords)
	s.log.Info("world.chunks.loaded",
		"event", "world.chunks.loaded",
		"map_id", DefaultWorldID,
		"center_chunk_x", center.X,
		"center_chunk_y", center.Y,
		"radius", radius,
		"chunk_count", len(coords),
		"duration_ms", time.Since(start).Milliseconds(),
	)
	return chunks, err
}

func visibleWorldChunks(center world.ChunkCoord, radius int) []world.ChunkCoord {
	worldChunks := worldgen.WorldSizeTiles / world.ChunkSize
	coords := make([]world.ChunkCoord, 0, worldChunks*worldChunks)
	seen := make(map[world.ChunkCoord]bool)
	for _, coord := range world.ChunksAround(center, radius) {
		wrapped := world.ChunkCoord{
			X: ((coord.X % worldChunks) + worldChunks) % worldChunks,
			Y: ((coord.Y % worldChunks) + worldChunks) % worldChunks,
		}
		if !seen[wrapped] {
			seen[wrapped] = true
			coords = append(coords, wrapped)
		}
	}
	return coords
}

func (s *WorldService) LoadViewport(ctx context.Context, viewport world.Viewport) ([]world.Chunk, error) {
	if viewport.Radius < 0 {
		return nil, apperror.WithFields(apperror.Validation, "viewport radius must be non-negative", map[string]string{"radius": "must be >= 0"})
	}
	if viewport.Radius > MaxViewportRadius {
		s.log.Warn("world.viewport.radius_oversized",
			"event", "world.viewport.radius_oversized",
			"requested_radius", viewport.Radius,
			"max_radius", MaxViewportRadius,
		)
		return nil, apperror.WithFields(apperror.Validation, "viewport radius is too large", map[string]string{"radius": "must be <= 96"})
	}
	centerChunk := world.ChunkForTile(viewport.Center)
	chunkRadius := (viewport.Radius + world.ChunkSize - 1) / world.ChunkSize
	if chunkRadius < DefaultChunkRadius {
		chunkRadius = DefaultChunkRadius
	}
	if chunkRadius > MaxChunkRadius {
		chunkRadius = MaxChunkRadius
	}
	s.log.Info("world.viewport.requested",
		"event", "world.viewport.requested",
		"map_id", DefaultWorldID,
		"tile_x", viewport.Center.X,
		"tile_y", viewport.Center.Y,
		"radius", viewport.Radius,
		"chunk_radius", chunkRadius,
	)
	return s.ListChunks(ctx, centerChunk, chunkRadius)
}
