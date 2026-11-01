package service

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/world"
)

func TestForestServiceChopAddsElderwoodHeartWhenDropSucceeds(t *testing.T) {
	ctx := context.Background()
	coord := world.Coord{X: 1, Y: 1}
	chunkCoord := world.ChunkForTile(coord)
	worlds := &forestWorldRepo{
		chunk: world.Chunk{
			MapID: DefaultWorldID,
			Coord: chunkCoord,
			Tiles: []world.Tile{{
				MapID:         DefaultWorldID,
				Coord:         coord,
				Chunk:         chunkCoord,
				Terrain:       world.TerrainForest,
				ForestDensity: 2,
			}},
		},
	}
	economyService := NewEconomyService(memory.NewEconomyRepo(), nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service := NewForestService(worlds, economyService, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.rareDrop = func() bool { return true }

	result, err := service.Chop(ctx, "p1", coord)
	if err != nil {
		t.Fatalf("expected forest chop to succeed: %v", err)
	}

	if result.Inventory.Items[economy.ResourceWood] != 1 {
		t.Fatalf("expected wood to increase to 1, got %d", result.Inventory.Items[economy.ResourceWood])
	}
	if result.Inventory.Items[economy.ResourceCoins] != 52 {
		t.Fatalf("expected coins to increase to 52, got %d", result.Inventory.Items[economy.ResourceCoins])
	}
	if result.Inventory.Items[economy.ResourceElderwoodHeart] != 1 {
		t.Fatalf("expected one elderwood heart, got %d", result.Inventory.Items[economy.ResourceElderwoodHeart])
	}
}

func TestForestChopPublishesOneAudibleResultWithCoordinateAndReason(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	coord := world.Coord{X: 2, Y: 3}
	chunkCoord := world.ChunkForTile(coord)
	worlds := &forestWorldRepo{chunk: world.Chunk{MapID: DefaultWorldID, Coord: chunkCoord, Tiles: []world.Tile{{
		MapID: DefaultWorldID, Coord: coord, Chunk: chunkCoord, Terrain: world.TerrainForest, ForestDensity: 2,
	}}}}
	economyService := NewEconomyService(memory.NewEconomyRepo(), nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service := NewForestService(worlds, economyService, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.rareDrop = func() bool { return false }
	bus := NewEventBus(4)
	service.SetEventBus(bus)
	events := bus.Subscribe(ctx)

	if _, err := service.Chop(ctx, "p1", coord); err != nil {
		t.Fatal(err)
	}
	select {
	case event := <-events:
		payload, ok := event.Payload.(TileChangedPayload)
		if !ok || event.Type != EventTileChanged || event.PlayerID != "p1" || event.ChunkID != world.ChunkID(DefaultWorldID, chunkCoord) || payload.Reason != "forest_cut" || payload.Tile.Coord != coord || event.CreatedAt.IsZero() {
			t.Fatalf("unexpected forest event: %#v", event)
		}
	default:
		t.Fatal("expected forest event")
	}
	select {
	case event := <-events:
		t.Fatalf("duplicate forest event: %#v", event)
	default:
	}
}

// Match the PostgreSQL JSONB NOT NULL constraint, which the memory repository does not enforce.
type forestJSONActionRepo struct {
	*memory.ActionRepo
}

func (r *forestJSONActionRepo) Append(ctx context.Context, item action.GameAction) error {
	if !json.Valid(item.Payload) {
		return errors.New("game_actions.payload must contain non-null valid JSON")
	}
	return r.ActionRepo.Append(ctx, item)
}

func TestForestServiceChopAllThreeStagesWithRegrowthQueue(t *testing.T) {
	ctx := context.Background()
	coord := world.Coord{X: 1, Y: 1}
	chunkCoord := world.ChunkForTile(coord)
	worlds := &forestWorldRepo{
		chunk: world.Chunk{
			MapID: DefaultWorldID,
			Coord: chunkCoord,
			Tiles: []world.Tile{{
				MapID:         DefaultWorldID,
				Coord:         coord,
				Chunk:         chunkCoord,
				Terrain:       world.TerrainForest,
				ForestDensity: world.MaxForestDensity,
			}},
		},
	}
	economyService := NewEconomyService(memory.NewEconomyRepo(), nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service := NewForestService(worlds, economyService, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.rareDrop = func() bool { return false }
	actions := &forestJSONActionRepo{ActionRepo: memory.NewActionRepo()}
	service.SetActionQueue(actions)
	now := time.Date(2026, 10, 30, 10, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }
	service.regrowthDelay = func() time.Duration { return 3 * time.Minute }

	var result ChopForestResult
	for range world.MaxForestDensity {
		var err error
		result, err = service.Chop(ctx, "p1", coord)
		if err != nil {
			t.Fatalf("expected forest chop to succeed: %v", err)
		}
	}

	if result.Tile.Terrain != world.TerrainGrass || result.Tile.ForestDensity != 0 {
		t.Fatalf("expected forest to be cleared, got terrain=%s density=%d", result.Tile.Terrain, result.Tile.ForestDensity)
	}
	if result.Inventory.Items[economy.ResourceCoins] != 56 {
		t.Fatalf("expected coins to increase by 2 for each stage to 56, got %d", result.Inventory.Items[economy.ResourceCoins])
	}
	if result.Inventory.Items[economy.ResourceWood] != 3 {
		t.Fatalf("expected wood from all three stages, got %d", result.Inventory.Items[economy.ResourceWood])
	}
	due, err := actions.FetchDue(ctx, now.Add(3*time.Minute), 10, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	if len(due) != 1 || due[0].Type != action.TypeRegrowForest || due[0].Target.ID != coordRef(coord) {
		t.Fatalf("expected exactly one regrowth action for the cleared tile, got %#v", due)
	}
}

func TestForestServiceChopUpdatesExactRequestedCoordinate(t *testing.T) {
	ctx := context.Background()
	requested := world.Coord{X: -1, Y: 1}
	wrappedNeighbor := world.Coord{X: 159, Y: 1}
	requestedChunk := world.ChunkForTile(requested)
	wrappedChunk := world.ChunkForTile(wrappedNeighbor)
	worlds := &forestMultiChunkRepo{
		chunks: map[world.ChunkCoord]world.Chunk{
			requestedChunk: {
				MapID: DefaultWorldID,
				Coord: requestedChunk,
				Tiles: []world.Tile{{
					MapID:         DefaultWorldID,
					Coord:         requested,
					Chunk:         requestedChunk,
					Terrain:       world.TerrainForest,
					ForestDensity: 3,
				}},
			},
			wrappedChunk: {
				MapID: DefaultWorldID,
				Coord: wrappedChunk,
				Tiles: []world.Tile{{
					MapID:         DefaultWorldID,
					Coord:         wrappedNeighbor,
					Chunk:         wrappedChunk,
					Terrain:       world.TerrainForest,
					ForestDensity: 3,
				}},
			},
		},
	}
	economyService := NewEconomyService(memory.NewEconomyRepo(), nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service := NewForestService(worlds, economyService, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.rareDrop = func() bool { return false }

	result, err := service.Chop(ctx, "p1", requested)
	if err != nil {
		t.Fatalf("expected forest chop to succeed: %v", err)
	}

	if result.Tile.Coord != requested {
		t.Fatalf("expected response for requested coord %#v, got %#v", requested, result.Tile.Coord)
	}
	if worlds.tile(requested).ForestDensity != 2 {
		t.Fatalf("expected requested tile density to become 2, got %d", worlds.tile(requested).ForestDensity)
	}
	if worlds.tile(wrappedNeighbor).ForestDensity != 3 {
		t.Fatalf("wrapped neighbor must not be changed, got density %d", worlds.tile(wrappedNeighbor).ForestDensity)
	}
}

func TestForestServiceSchedulesRegrowthAfterClearingForest(t *testing.T) {
	ctx := context.Background()
	coord := world.Coord{X: 8, Y: 8}
	chunkCoord := world.ChunkForTile(coord)
	worlds := &forestWorldRepo{
		chunk: world.Chunk{
			MapID: DefaultWorldID,
			Coord: chunkCoord,
			Tiles: []world.Tile{{
				MapID:         DefaultWorldID,
				Coord:         coord,
				Chunk:         chunkCoord,
				Terrain:       world.TerrainForest,
				ForestDensity: 1,
			}},
		},
	}
	actionRepo := memory.NewActionRepo()
	economyService := NewEconomyService(memory.NewEconomyRepo(), nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service := NewForestService(worlds, economyService, slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 10, 12, 10, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }
	service.regrowthDelay = func() time.Duration { return 3 * time.Minute }
	service.rareDrop = func() bool { return false }
	service.SetActionQueue(actionRepo)

	if _, err := service.Chop(ctx, "p1", coord); err != nil {
		t.Fatalf("chop: %v", err)
	}

	early, err := actionRepo.FetchDue(ctx, now.Add(2*time.Minute), 10, time.Second)
	if err != nil {
		t.Fatalf("fetch early actions: %v", err)
	}
	if len(early) != 0 {
		t.Fatalf("expected no due actions before delay, got %d", len(early))
	}
	due, err := actionRepo.FetchDue(ctx, now.Add(3*time.Minute), 10, time.Second)
	if err != nil {
		t.Fatalf("fetch due actions: %v", err)
	}
	if len(due) != 1 || due[0].Type != action.TypeRegrowForest {
		t.Fatalf("expected one forest regrowth action, got %#v", due)
	}
}

func TestForestServiceRegrowsOnlyOnFreeGrassTile(t *testing.T) {
	ctx := context.Background()
	source := world.Coord{X: 8, Y: 8}
	chunkCoord := world.ChunkForTile(source)
	occupiedGrass := world.Coord{X: 9, Y: 8}
	freeGrass := world.Coord{X: 10, Y: 8}
	worlds := &forestWorldRepo{
		chunk: world.Chunk{
			MapID: DefaultWorldID,
			Coord: chunkCoord,
			Tiles: []world.Tile{
				{MapID: DefaultWorldID, Coord: source, Chunk: chunkCoord, Terrain: world.TerrainGrass},
				{MapID: DefaultWorldID, Coord: occupiedGrass, Chunk: chunkCoord, Terrain: world.TerrainGrass},
				{MapID: DefaultWorldID, Coord: freeGrass, Chunk: chunkCoord, Terrain: world.TerrainGrass},
				{MapID: DefaultWorldID, Coord: world.Coord{X: 8, Y: 9}, Chunk: chunkCoord, Terrain: world.TerrainWater},
			},
		},
	}
	buildingRepo := memory.NewBuildingRepo()
	if err := buildingRepo.Create(ctx, building.Building{
		ID:        "b1",
		MapID:     DefaultWorldID,
		OwnerID:   "p1",
		Type:      building.TypeTownHall,
		State:     building.StateActive,
		Tile:      occupiedGrass,
		Footprint: building.Footprint{Width: 1, Height: 1},
	}); err != nil {
		t.Fatalf("create building: %v", err)
	}
	economyService := NewEconomyService(memory.NewEconomyRepo(), buildingRepo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service := NewForestService(worlds, economyService, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetBuildingRepository(buildingRepo)

	regrown, ok, err := service.RegrowAround(ctx, source, time.Now().UTC())
	if err != nil {
		t.Fatalf("regrow: %v", err)
	}
	if !ok {
		t.Fatal("expected forest to regrow")
	}
	if regrown.Coord != freeGrass {
		t.Fatalf("expected forest to regrow on free grass tile, got %#v", regrown.Coord)
	}
	if worlds.tile(occupiedGrass).Terrain != world.TerrainGrass {
		t.Fatal("occupied grass tile must not be replaced by forest")
	}
	if worlds.tile(freeGrass).Terrain != world.TerrainForest || worlds.tile(freeGrass).ForestDensity != world.MaxForestDensity {
		t.Fatal("free grass tile was not restored to full forest")
	}
}

func TestForestServiceRegrowthReadsFreshTerrain(t *testing.T) {
	ctx := context.Background()
	source := world.Coord{X: 8, Y: 8}
	staleGrass := world.Coord{X: 9, Y: 8}
	freshGrass := world.Coord{X: 10, Y: 8}
	chunkCoord := world.ChunkForTile(source)
	worlds := &forestFreshWorldRepo{forestWorldRepo: forestWorldRepo{chunk: world.Chunk{
		MapID: DefaultWorldID,
		Coord: chunkCoord,
		Tiles: []world.Tile{
			{MapID: DefaultWorldID, Coord: source, Chunk: chunkCoord, Terrain: world.TerrainGrass},
			{MapID: DefaultWorldID, Coord: staleGrass, Chunk: chunkCoord, Terrain: world.TerrainWater},
			{MapID: DefaultWorldID, Coord: freshGrass, Chunk: chunkCoord, Terrain: world.TerrainGrass},
		},
	}}}
	service := NewForestService(worlds, nil, slog.New(slog.NewTextHandler(io.Discard, nil)))

	regrown, ok, err := service.RegrowAround(ctx, source, time.Now().UTC())
	if err != nil || !ok {
		t.Fatalf("regrow: tile=%#v ok=%t err=%v", regrown, ok, err)
	}
	if regrown.Coord != freshGrass {
		t.Fatalf("expected current grass tile %v, got %v", freshGrass, regrown.Coord)
	}
}

func TestForestChopRewardsCanIncludeElderwoodHeart(t *testing.T) {
	rewards := forestChopRewards(true)

	if len(rewards) != 3 {
		t.Fatalf("expected wood, coins and elderwood heart rewards, got %d", len(rewards))
	}
	assertReward(t, rewards, economy.ResourceWood, 1)
	assertReward(t, rewards, economy.ResourceCoins, 2)
	assertReward(t, rewards, economy.ResourceElderwoodHeart, 1)
}

func TestForestChopRewardsUsuallyOnlyWood(t *testing.T) {
	rewards := forestChopRewards(false)

	if len(rewards) != 2 {
		t.Fatalf("expected wood and coins rewards, got %d", len(rewards))
	}
	assertReward(t, rewards, economy.ResourceWood, 1)
	assertReward(t, rewards, economy.ResourceCoins, 2)
}

func TestElderwoodHeartDropChanceIsOneHundredthPercent(t *testing.T) {
	if elderwoodHeartDropChance != 0.0001 {
		t.Fatalf("expected 0.01%% drop chance, got %.8f", elderwoodHeartDropChance)
	}
}

func assertReward(t *testing.T, rewards []economy.ResourceAmount, resource economy.ResourceType, amount int) {
	t.Helper()
	for _, reward := range rewards {
		if reward.Resource == resource {
			if reward.Amount != amount {
				t.Fatalf("expected %s amount %d, got %d", resource, amount, reward.Amount)
			}
			return
		}
	}
	t.Fatalf("expected %s reward", resource)
}

type forestWorldRepo struct {
	chunk world.Chunk
}

type forestFreshWorldRepo struct {
	forestWorldRepo
}

func (r *forestFreshWorldRepo) GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	stale := r.chunk
	stale.Tiles = append([]world.Tile(nil), stale.Tiles...)
	stale.Tiles[1].Terrain = world.TerrainGrass
	return []world.Chunk{stale}, nil
}

func (r *forestWorldRepo) GetMap(ctx context.Context, id string) (world.WorldMap, error) {
	_ = ctx
	return world.WorldMap{ID: id}, nil
}

func (r *forestWorldRepo) GetOrCreateChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (world.Chunk, bool, error) {
	_ = ctx
	_ = mapID
	_ = coord
	return r.chunk, true, nil
}

func (r *forestWorldRepo) GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	_ = ctx
	_ = mapID
	_ = coords
	return []world.Chunk{r.chunk}, nil
}

func (r *forestWorldRepo) GetOrCreateChunksFresh(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	return r.GetOrCreateChunks(ctx, mapID, coords)
}

func (r *forestWorldRepo) UpdateTile(ctx context.Context, tile world.Tile) error {
	_ = ctx
	for index := range r.chunk.Tiles {
		if r.chunk.Tiles[index].Coord == tile.Coord {
			r.chunk.Tiles[index] = tile
			return nil
		}
	}
	r.chunk.Tiles = append(r.chunk.Tiles, tile)
	return nil
}

func (r *forestWorldRepo) tile(coord world.Coord) world.Tile {
	for _, tile := range r.chunk.Tiles {
		if tile.Coord == coord {
			return tile
		}
	}
	return world.Tile{}
}

type forestMultiChunkRepo struct {
	chunks map[world.ChunkCoord]world.Chunk
}

func (r *forestMultiChunkRepo) GetMap(ctx context.Context, id string) (world.WorldMap, error) {
	_ = ctx
	return world.WorldMap{ID: id}, nil
}

func (r *forestMultiChunkRepo) GetOrCreateChunk(ctx context.Context, mapID string, coord world.ChunkCoord) (world.Chunk, bool, error) {
	_ = ctx
	_ = mapID
	chunk, ok := r.chunks[coord]
	if !ok {
		return world.Chunk{MapID: DefaultWorldID, Coord: coord}, false, nil
	}
	return chunk, true, nil
}

func (r *forestMultiChunkRepo) GetOrCreateChunks(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	_ = ctx
	_ = mapID
	chunks := make([]world.Chunk, 0, len(coords))
	for _, coord := range coords {
		if chunk, ok := r.chunks[coord]; ok {
			chunks = append(chunks, chunk)
		}
	}
	return chunks, nil
}

func (r *forestMultiChunkRepo) GetOrCreateChunksFresh(ctx context.Context, mapID string, coords []world.ChunkCoord) ([]world.Chunk, error) {
	return r.GetOrCreateChunks(ctx, mapID, coords)
}

func (r *forestMultiChunkRepo) UpdateTile(ctx context.Context, tile world.Tile) error {
	_ = ctx
	chunk := r.chunks[tile.Chunk]
	for index := range chunk.Tiles {
		if chunk.Tiles[index].Coord == tile.Coord {
			chunk.Tiles[index] = tile
			r.chunks[tile.Chunk] = chunk
			return nil
		}
	}
	chunk.Tiles = append(chunk.Tiles, tile)
	r.chunks[tile.Chunk] = chunk
	return nil
}

func (r *forestMultiChunkRepo) tile(coord world.Coord) world.Tile {
	chunk := r.chunks[world.ChunkForTile(coord)]
	for _, tile := range chunk.Tiles {
		if tile.Coord == coord {
			return tile
		}
	}
	return world.Tile{}
}
