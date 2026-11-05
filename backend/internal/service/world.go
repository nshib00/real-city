package service

import (
	"context"
	"encoding/json"
	"log/slog"
	"sync"
	"sync/atomic"
	"time"

	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

const (
	DefaultWorldID     = "dev-world"
	MaxChunkRadius     = 3
	MaxViewportRadius  = 96
	DefaultChunkRadius = 1
)

type WorldService struct {
	repo  WorldRepository
	log   *slog.Logger
	cache interface {
		Get(context.Context, string) ([]byte, bool, error)
		Set(context.Context, string, []byte, time.Duration) error
		Delete(context.Context, string) error
	}
	cacheWarningAt atomic.Int64
	chunkLocks     sync.Map
}

type chunkCacheState struct {
	mu sync.Mutex
	generation uint64
}

func (s *WorldService) chunkState(key string) *chunkCacheState {
	state, _ := s.chunkLocks.LoadOrStore(key, &chunkCacheState{})
	return state.(*chunkCacheState)
}

func (s *WorldService) warnCacheFailure(event string, err error) {
	now := time.Now().UnixNano()
	last := s.cacheWarningAt.Load()
	if now-last >= int64(5*time.Second) && s.cacheWarningAt.CompareAndSwap(last, now) {
		s.log.Warn(event, "error", err)
	}
}

func (s *WorldService) SetCache(cache interface {
	Get(context.Context, string) ([]byte, bool, error)
	Set(context.Context, string, []byte, time.Duration) error
	Delete(context.Context, string) error
}) {
	s.cache = cache
}

func (s *WorldService) InvalidateEvent(ctx context.Context, event Event) {
	if s.cache == nil || event.ChunkID == "" {
		return
	}
	switch event.Type {
	case EventTileChanged, EventBuildingPlaced, EventBuildingUpdated, EventBuildingRemoved,
		EventResourceChanged, EventMonsterSpawned, EventMonsterMoved, EventMonsterAttacked,
		EventMonsterDamaged, EventMonsterDied, EventMonsterDespawned:
		key := "real-city:cache:chunk:" + event.ChunkID
		state := s.chunkState(key)
		state.mu.Lock()
		defer state.mu.Unlock()
		state.generation++
		if err := s.cache.Delete(ctx, key); err != nil {
			s.warnCacheFailure("world.cache.invalidate_failed", err)
		} else {
			s.log.Debug("world.cache.delete", "chunk_id", event.ChunkID)
		}
	}
}

func NewWorldService(repo WorldRepository, log *slog.Logger) *WorldService {
	return &WorldService{repo: repo, log: log}
}

func (s *WorldService) GetWorld(ctx context.Context) (world.WorldMap, error) {
	return s.repo.GetMap(ctx, DefaultWorldID)
}

func (s *WorldService) GetChunk(ctx context.Context, coord world.ChunkCoord) (world.Chunk, error) {
	coord = world.NormalizeChunk(coord)
	if s.cache != nil {
		state := s.chunkState(chunkCacheKey(DefaultWorldID, coord))
		state.mu.Lock()
		defer state.mu.Unlock()
		raw, hit, cacheErr := s.cache.Get(ctx, chunkCacheKey(DefaultWorldID, coord))
		if cacheErr != nil {
			s.warnCacheFailure("world.cache.get_failed", cacheErr)
		} else if hit {
			var chunk world.Chunk
			if json.Unmarshal(raw, &chunk) == nil && chunk.MapID == DefaultWorldID && chunk.Coord == coord {
				s.log.Debug("world.cache.hit", "chunk_id", world.ChunkID(DefaultWorldID, coord))
				return chunk, nil
			}
			s.log.Warn("world.cache.invalid_value", "chunk_id", world.ChunkID(DefaultWorldID, coord))
		} else {
			s.log.Debug("world.cache.miss", "chunk_id", world.ChunkID(DefaultWorldID, coord))
		}
	}
	start := time.Now()
	chunk, hit, err := s.repo.GetOrCreateChunk(ctx, DefaultWorldID, coord)
	if elapsed := time.Since(start); elapsed >= 250*time.Millisecond {
		s.log.Warn("world.chunk.slow_query", "chunk_id", world.ChunkID(DefaultWorldID, coord), "duration_ms", elapsed.Milliseconds())
	}
	if err == nil && s.cache != nil {
		if raw, marshalErr := json.Marshal(chunk); marshalErr == nil {
			if cacheErr := s.cache.Set(ctx, chunkCacheKey(DefaultWorldID, coord), raw, 2*time.Second); cacheErr != nil {
				s.warnCacheFailure("world.cache.set_failed", cacheErr)
			} else {
				s.log.Debug("world.cache.set", "chunk_id", world.ChunkID(DefaultWorldID, coord))
			}
		}
	}
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
	chunks, err := s.listChunksCached(ctx, coords)
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

func (s *WorldService) listChunksCached(ctx context.Context, coords []world.ChunkCoord) ([]world.Chunk, error) {
	cache, ok := s.cache.(interface { GetMany(context.Context, []string) (map[string][]byte, error) })
	if !ok { return s.repo.GetOrCreateChunks(ctx, DefaultWorldID, coords) }
	keys := make([]string, len(coords))
	for i, coord := range coords { keys[i] = chunkCacheKey(DefaultWorldID, coord) }
	raw, err := cache.GetMany(ctx, keys)
	if err != nil {
		s.warnCacheFailure("world.cache.get_many_failed", err)
		return s.repo.GetOrCreateChunks(ctx, DefaultWorldID, coords)
	}
	result := make(map[world.ChunkCoord]world.Chunk, len(coords))
	missing := make([]world.ChunkCoord, 0, len(coords))
	versions := make(map[world.ChunkCoord]uint64, len(coords))
	for i, coord := range coords {
		var chunk world.Chunk
		if value, exists := raw[keys[i]]; exists && json.Unmarshal(value, &chunk) == nil && chunk.MapID == DefaultWorldID && chunk.Coord == coord {
			result[coord] = chunk
			continue
		}
		missing = append(missing, coord)
		state := s.chunkState(keys[i])
		state.mu.Lock()
		versions[coord] = state.generation
		state.mu.Unlock()
	}
	s.log.Debug("world.cache.batch", "hits", len(coords)-len(missing), "misses", len(missing))
	if len(missing) > 0 {
		loaded, err := s.repo.GetOrCreateChunks(ctx, DefaultWorldID, missing)
		if err != nil { return nil, err }
		for _, chunk := range loaded {
			result[chunk.Coord] = chunk
			value, marshalErr := json.Marshal(chunk)
			if marshalErr != nil { continue }
			key := chunkCacheKey(DefaultWorldID, chunk.Coord)
			state := s.chunkState(key)
			state.mu.Lock()
			if state.generation == versions[chunk.Coord] {
				if err := s.cache.Set(ctx, key, value, 2*time.Second); err != nil { s.warnCacheFailure("world.cache.set_failed", err) }
			}
			state.mu.Unlock()
		}
	}
	chunks := make([]world.Chunk, 0, len(coords))
	for _, coord := range coords { chunks = append(chunks, result[coord]) }
	return chunks, nil
}

func visibleWorldChunks(center world.ChunkCoord, radius int) []world.ChunkCoord {
	return world.UniqueChunks(world.ChunksAround(world.NormalizeChunk(center), radius))
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
