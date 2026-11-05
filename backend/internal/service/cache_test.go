package service

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"sync"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/world"
)

type blockingWorldCache struct {
	mu         sync.Mutex
	values     map[string][]byte
	setStarted chan struct{}
	releaseSet chan struct{}
}

func (c *blockingWorldCache) Get(_ context.Context, key string) ([]byte, bool, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	value, ok := c.values[key]
	return value, ok, nil
}
func (c *blockingWorldCache) Set(_ context.Context, key string, value []byte, _ time.Duration) error {
	close(c.setStarted)
	<-c.releaseSet
	c.mu.Lock()
	defer c.mu.Unlock()
	c.values[key] = value
	return nil
}
func (c *blockingWorldCache) Delete(_ context.Context, key string) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.values, key)
	return nil
}

func TestChunkInvalidationCannotRaceBehindCacheSet(t *testing.T) {
	s := NewWorldService(memory.NewWorldRepo(), slog.New(slog.NewTextHandler(io.Discard, nil)))
	cache := &blockingWorldCache{values: make(map[string][]byte), setStarted: make(chan struct{}), releaseSet: make(chan struct{})}
	s.SetCache(cache)
	coord := world.ChunkCoord{X: 1, Y: 1}
	loaded := make(chan error, 1)
	go func() { _, err := s.GetChunk(context.Background(), coord); loaded <- err }()
	<-cache.setStarted
	invalidated := make(chan struct{})
	go func() {
		s.InvalidateEvent(context.Background(), Event{Type: EventTileChanged, ChunkID: world.ChunkID(DefaultWorldID, coord)})
		close(invalidated)
	}()
	select {
	case <-invalidated:
		t.Fatal("invalidation passed an unfinished cache set")
	case <-time.After(10 * time.Millisecond):
	}
	close(cache.releaseSet)
	if err := <-loaded; err != nil {
		t.Fatal(err)
	}
	<-invalidated
	cache.mu.Lock()
	defer cache.mu.Unlock()
	if len(cache.values) != 0 {
		t.Fatal("stale chunk remained cached after invalidation")
	}
}

type countingWorldRepo struct {
	WorldRepository
	loads int
}

type countingBatchWorldRepo struct {
	WorldRepository
	loads []int
}

func (r *countingBatchWorldRepo) GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	r.loads = append(r.loads, len(coords))
	return r.WorldRepository.GetOrCreateChunks(ctx, mapID, coords)
}

type batchWorldCache struct { testWorldCache }

func (c *batchWorldCache) GetMany(_ context.Context, keys []string) (map[string][]byte, error) {
	result := make(map[string][]byte)
	for _, key := range keys { if value, ok := c.values[key]; ok { result[key] = value } }
	return result, nil
}

func TestChunkBatchCacheLoadsOnlyChangedChunk(t *testing.T) {
	repo := &countingBatchWorldRepo{WorldRepository: memory.NewWorldRepo()}
	s := NewWorldService(repo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	cache := &batchWorldCache{testWorldCache{values: make(map[string][]byte)}}
	s.SetCache(cache)
	center := world.ChunkCoord{X: 0, Y: 0}
	for i := 0; i < 2; i++ {
		chunks, err := s.ListChunks(context.Background(), center, 1)
		if err != nil || len(chunks) != 9 { t.Fatalf("load %d: chunks=%d err=%v", i, len(chunks), err) }
	}
	if len(repo.loads) != 1 || repo.loads[0] != 9 { t.Fatalf("batch repo calls: %v", repo.loads) }
	s.InvalidateEvent(context.Background(), Event{Type: EventTileChanged, ChunkID: world.ChunkID(DefaultWorldID, center)})
	if _, err := s.ListChunks(context.Background(), center, 1); err != nil { t.Fatal(err) }
	if len(repo.loads) != 2 || repo.loads[1] != 1 { t.Fatalf("changed batch repo calls: %v", repo.loads) }
}

func (r *countingWorldRepo) GetOrCreateChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (world.Chunk, bool, error) {
	r.loads++
	return r.WorldRepository.GetOrCreateChunk(ctx, mapID, coord)
}

type failingWorldCache struct {
	getErr, setErr, deleteErr error
}

func (c failingWorldCache) Get(context.Context, string) ([]byte, bool, error) {
	return nil, false, c.getErr
}
func (c failingWorldCache) Set(context.Context, string, []byte, time.Duration) error { return c.setErr }
func (c failingWorldCache) Delete(context.Context, string) error                     { return c.deleteErr }

func TestChunkCacheAsideAndDegradedFallback(t *testing.T) {
	repo := &countingWorldRepo{WorldRepository: memory.NewWorldRepo()}
	s := NewWorldService(repo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	cache := &testWorldCache{values: make(map[string][]byte)}
	s.SetCache(cache)
	coord := world.ChunkCoord{X: 3, Y: 2}
	for i := 0; i < 2; i++ {
		if _, err := s.GetChunk(context.Background(), coord); err != nil {
			t.Fatal(err)
		}
	}
	if repo.loads != 1 {
		t.Fatalf("repo loads = %d, want 1", repo.loads)
	}
	s.InvalidateEvent(context.Background(), Event{Type: EventResourceChanged, ChunkID: world.ChunkID(DefaultWorldID, coord)})
	if _, err := s.GetChunk(context.Background(), coord); err != nil {
		t.Fatal(err)
	}
	if repo.loads != 2 {
		t.Fatalf("repo loads after invalidation = %d, want 2", repo.loads)
	}
	s.SetCache(failingWorldCache{getErr: errors.New("offline"), setErr: errors.New("offline"), deleteErr: errors.New("offline")})
	if _, err := s.GetChunk(context.Background(), coord); err != nil {
		t.Fatalf("SQL fallback failed: %v", err)
	}
	if repo.loads != 3 {
		t.Fatalf("repo loads after outage = %d, want 3", repo.loads)
	}
}
