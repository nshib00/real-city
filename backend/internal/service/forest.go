package service

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"
	"strconv"
	"strings"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

const elderwoodHeartDropChance = 0.0001
const forestRegrowthRadius = 4
const forestRegrowthTargetPercent = 30

var (
	forestRegrowthMinDelay = 3 * time.Minute
	forestRegrowthMaxDelay = 5 * time.Minute
)

type ChopForestResult struct {
	Tile      world.Tile
	Inventory economy.Inventory
}

type ForestService struct {
	worlds        WorldRepository
	buildings     BuildingRepository
	economy       *EconomyService
	log           *slog.Logger
	events        *EventBus
	actions       ActionRepository
	experience    *ExperienceService
	rareDrop      func() bool
	regrowthDelay func() time.Duration
	now           func() time.Time
}

func NewForestService(worlds WorldRepository, economyService *EconomyService, log *slog.Logger) *ForestService {
	return &ForestService{
		worlds:        worlds,
		economy:       economyService,
		log:           log,
		rareDrop:      func() bool { return rand.Float64() < elderwoodHeartDropChance },
		regrowthDelay: randomForestRegrowthDelay,
		now:           func() time.Time { return time.Now().UTC() },
	}
}

func (s *ForestService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *ForestService) SetBuildingRepository(buildings BuildingRepository) {
	s.buildings = buildings
}

func (s *ForestService) SetActionQueue(actions ActionRepository) {
	s.actions = actions
}

func (s *ForestService) SetExperience(experience *ExperienceService) {
	s.experience = experience
}

func (s *ForestService) Chop(ctx context.Context, playerID player.ID, coord world.Coord) (ChopForestResult, error) {
	chunkCoord := world.ChunkForTile(coord)
	chunk, _, err := s.worlds.GetOrCreateChunk(ctx, DefaultWorldID, chunkCoord)
	if err != nil {
		return ChopForestResult{}, err
	}
	tile, ok := findTile(chunk, coord)
	if !ok {
		return ChopForestResult{}, apperror.New(apperror.NotFound, "tile not found")
	}
	nextTile, chopped := world.ChopForest(tile)
	if !chopped {
		return ChopForestResult{}, apperror.New(apperror.Conflict, "tile has no forest to chop")
	}
	if err := s.worlds.UpdateTile(ctx, nextTile); err != nil {
		return ChopForestResult{}, err
	}
	if nextTile.Terrain == world.TerrainGrass && nextTile.ForestDensity == 0 {
		if err := s.scheduleRegrowth(ctx, nextTile); err != nil {
			return ChopForestResult{}, err
		}
	}
	inventory, _, err := s.economy.Add(ctx, playerID, forestChopRewards(s.rareDrop()), "forest:chop")
	if err != nil {
		return ChopForestResult{}, err
	}
	if s.experience != nil {
		key := fmt.Sprintf("forest:chop:%d:%d:%d", coord.X, coord.Y, s.now().UnixNano())
		if err := s.experience.Award(ctx, playerID, 1, "forest:chop", key); err != nil {
			return ChopForestResult{}, err
		}
	}
	if s.events != nil {
		s.events.Publish(Event{
			Type:     EventTileChanged,
			ChunkID:  world.ChunkID(nextTile.MapID, nextTile.Chunk),
			PlayerID: playerID,
			Payload:  TileChangedPayload{Tile: nextTile, Reason: "forest_cut"},
		})
	}
	s.log.Info("world.forest.chopped", "event", "world.forest.chopped", "player_id", playerID, "tile_x", coord.X, "tile_y", coord.Y, "forest_density", nextTile.ForestDensity)
	return ChopForestResult{Tile: nextTile, Inventory: inventory}, nil
}

func (s *ForestService) RegrowAround(ctx context.Context, source world.Coord, now time.Time) (world.Tile, bool, error) {
	chunks, err := s.worlds.GetOrCreateChunksFresh(ctx, DefaultWorldID, chunksAroundSquare(source, forestRegrowthRadius))
	if err != nil {
		return world.Tile{}, false, err
	}
	occupied, err := s.occupiedTiles(ctx, chunks)
	if err != nil {
		return world.Tile{}, false, err
	}

	var selected world.Tile
	bestScore := -1
	freeNatural := 0
	forestCount := 0
	candidates := make([]world.Tile, 0)
	for _, chunk := range chunks {
		for _, tile := range chunk.Tiles {
			if !withinSquare(tile.Coord, source, forestRegrowthRadius) || occupied[tile.Coord] {
				continue
			}
			if tile.Terrain == world.TerrainForest {
				freeNatural++
				forestCount++
				continue
			}
			if tile.Terrain != world.TerrainGrass {
				continue
			}
			freeNatural++
			if tile.Coord == source {
				continue
			}
			candidates = append(candidates, tile)
		}
	}
	targetBoost := forestCount*100 < max(1, freeNatural)*forestRegrowthTargetPercent
	for _, tile := range candidates {
		score := forestRegrowthScore(tile.Coord, source, chunks, occupied, targetBoost)
		if score > bestScore || selected.MapID == "" {
			selected = tile
			bestScore = score
		}
	}
	if selected.MapID == "" {
		return world.Tile{}, false, nil
	}

	selected.Terrain = world.TerrainForest
	selected.ForestDensity = world.MaxForestDensity
	if err := s.worlds.UpdateTile(ctx, selected); err != nil {
		return world.Tile{}, false, err
	}
	if s.events != nil {
		s.events.Publish(Event{
			Type:    EventTileChanged,
			ChunkID: world.ChunkID(selected.MapID, selected.Chunk),
			Payload: TileChangedPayload{Tile: selected, Reason: "forest_regrown"},
		})
	}
	s.log.Info("world.forest.regrown", "event", "world.forest.regrown", "tile_x", selected.Coord.X, "tile_y", selected.Coord.Y, "source_x", source.X, "source_y", source.Y, "free_natural", freeNatural, "forest_count", forestCount, "at", now)
	return selected, true, nil
}

func (s *ForestService) HandleRegrowthAction(ctx context.Context, item action.GameAction, now time.Time) error {
	source, err := parseCoordRef(item.Target.ID)
	if err != nil {
		return err
	}
	_, _, err = s.RegrowAround(ctx, source, now)
	return err
}

func (s *ForestService) scheduleRegrowth(ctx context.Context, tile world.Tile) error {
	if s.actions == nil {
		return nil
	}
	now := s.now()
	dueAt := now.Add(s.regrowthDelay())
	coord := coordRef(tile.Coord)
	return s.actions.Append(ctx, action.NewGameAction(
		action.ID(fmt.Sprintf("act_forest_regrow_%s_%d", coord, dueAt.UnixNano())),
		action.TypeRegrowForest,
		fmt.Sprintf("forest:%s:regrow:%d", coord, dueAt.UnixNano()),
		action.ObjectRef{},
		action.ObjectRef{ID: coord, Type: "world_tile"},
		dueAt,
		now,
	))
}

func forestChopRewards(elderwoodHeart bool) []economy.ResourceAmount {
	rewards := []economy.ResourceAmount{
		{Resource: economy.ResourceWood, Amount: 1},
		{Resource: economy.ResourceCoins, Amount: 2},
	}
	if elderwoodHeart {
		rewards = append(rewards, economy.ResourceAmount{Resource: economy.ResourceElderwoodHeart, Amount: 1})
	}
	return rewards
}

func (s *ForestService) occupiedTiles(ctx context.Context, chunks []world.Chunk) (map[world.Coord]bool, error) {
	occupied := make(map[world.Coord]bool)
	if s.buildings == nil {
		return occupied, nil
	}
	seenChunks := make(map[world.ChunkCoord]bool, len(chunks))
	for _, chunk := range chunks {
		if seenChunks[chunk.Coord] {
			continue
		}
		seenChunks[chunk.Coord] = true
		buildings, err := s.buildings.ListByChunk(ctx, chunk.MapID, chunk.Coord)
		if err != nil {
			return nil, err
		}
		for _, item := range buildings {
			if item.State == building.StateRuined {
				continue
			}
			for _, coord := range item.OccupiedTiles() {
				occupied[coord] = true
			}
		}
	}
	return occupied, nil
}

func forestRegrowthScore(coord world.Coord, source world.Coord, chunks []world.Chunk, occupied map[world.Coord]bool, preferForestCluster bool) int {
	score := 0
	distance := abs(coord.X-source.X) + abs(coord.Y-source.Y)
	score -= distance
	for _, neighbor := range []world.Coord{
		{X: coord.X + 1, Y: coord.Y},
		{X: coord.X - 1, Y: coord.Y},
		{X: coord.X, Y: coord.Y + 1},
		{X: coord.X, Y: coord.Y - 1},
	} {
		if occupied[neighbor] {
			score -= 3
			continue
		}
		if tile, ok := tileFromChunks(chunks, neighbor); ok && tile.Terrain == world.TerrainForest {
			if preferForestCluster {
				score += 5
			} else {
				score--
			}
		}
	}
	return score
}

func tileFromChunks(chunks []world.Chunk, coord world.Coord) (world.Tile, bool) {
	for _, chunk := range chunks {
		for _, tile := range chunk.Tiles {
			if tile.Coord == coord {
				return tile, true
			}
		}
	}
	return world.Tile{}, false
}

func chunksAroundSquare(center world.Coord, radius int) []world.ChunkCoord {
	minChunk := world.ChunkForTile(world.Coord{X: center.X - radius, Y: center.Y - radius})
	maxChunk := world.ChunkForTile(world.Coord{X: center.X + radius, Y: center.Y + radius})
	chunks := make([]world.ChunkCoord, 0, (maxChunk.X-minChunk.X+1)*(maxChunk.Y-minChunk.Y+1))
	for y := minChunk.Y; y <= maxChunk.Y; y++ {
		for x := minChunk.X; x <= maxChunk.X; x++ {
			chunks = append(chunks, world.ChunkCoord{X: x, Y: y})
		}
	}
	return chunks
}

func withinSquare(coord world.Coord, center world.Coord, radius int) bool {
	return abs(coord.X-center.X) <= radius && abs(coord.Y-center.Y) <= radius
}

func coordRef(coord world.Coord) string {
	return fmt.Sprintf("%d:%d", coord.X, coord.Y)
}

func parseCoordRef(value string) (world.Coord, error) {
	parts := strings.Split(value, ":")
	if len(parts) != 2 {
		return world.Coord{}, apperror.New(apperror.Validation, "invalid forest regrowth target")
	}
	x, err := strconv.Atoi(parts[0])
	if err != nil {
		return world.Coord{}, apperror.New(apperror.Validation, "invalid forest regrowth target")
	}
	y, err := strconv.Atoi(parts[1])
	if err != nil {
		return world.Coord{}, apperror.New(apperror.Validation, "invalid forest regrowth target")
	}
	return world.Coord{X: x, Y: y}, nil
}

func randomForestRegrowthDelay() time.Duration {
	spread := forestRegrowthMaxDelay - forestRegrowthMinDelay
	if spread <= 0 {
		return forestRegrowthMinDelay
	}
	return forestRegrowthMinDelay + time.Duration(rand.Int63n(int64(spread)+1))
}

func abs(value int) int {
	if value < 0 {
		return -value
	}
	return value
}
