package service

import (
	"context"
	"log/slog"
	"math/rand"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

const elderwoodHeartDropChance = 0.0001

type ChopForestResult struct {
	Tile      world.Tile
	Inventory economy.Inventory
}

type ForestService struct {
	worlds   WorldRepository
	economy  *EconomyService
	log      *slog.Logger
	events   *EventBus
	rareDrop func() bool
}

func NewForestService(worlds WorldRepository, economyService *EconomyService, log *slog.Logger) *ForestService {
	return &ForestService{
		worlds:   worlds,
		economy:  economyService,
		log:      log,
		rareDrop: func() bool { return rand.Float64() < elderwoodHeartDropChance },
	}
}

func (s *ForestService) SetEventBus(events *EventBus) {
	s.events = events
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
	inventory, _, err := s.economy.Add(ctx, playerID, forestChopRewards(s.rareDrop()), "forest:chop")
	if err != nil {
		return ChopForestResult{}, err
	}
	if s.events != nil {
		s.events.Publish(Event{
			Type:     EventTileChanged,
			ChunkID:  world.ChunkID(nextTile.MapID, nextTile.Chunk),
			PlayerID: playerID,
			Payload:  TileChangedPayload{Tile: nextTile},
		})
	}
	s.log.Info("world.forest.chopped", "event", "world.forest.chopped", "player_id", playerID, "tile_x", coord.X, "tile_y", coord.Y, "forest_density", nextTile.ForestDensity)
	return ChopForestResult{Tile: nextTile, Inventory: inventory}, nil
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
