package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type BuildingService struct {
	buildings BuildingRepository
	worlds    WorldRepository
	log       *slog.Logger
	now       func() time.Time
	rules     building.BuildRules
	events    *EventBus
	economy   *EconomyService
}

type PlaceBuildingInput struct {
	PlayerID player.ID
	Type     building.Type
	Tile     world.Coord
}

func NewBuildingService(buildings BuildingRepository, worlds WorldRepository, log *slog.Logger) *BuildingService {
	return &BuildingService{buildings: buildings, worlds: worlds, log: log, now: func() time.Time { return time.Now().UTC() }, rules: building.BuildRules{BaseLimit: 8}}
}

func (s *BuildingService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *BuildingService) SetEconomy(economyService *EconomyService) {
	s.economy = economyService
}

func (s *BuildingService) Catalog(ctx context.Context) ([]catalog.BuildingType, error) {
	_ = ctx
	return catalog.FirstLevelBuildings(), nil
}

func (s *BuildingService) Place(ctx context.Context, input PlaceBuildingInput) (building.Building, error) {
	spec, ok := catalog.GetBuilding(input.Type)
	if !ok {
		return building.Building{}, apperror.WithFields(apperror.Validation, "unknown building type", map[string]string{"type": string(input.Type)})
	}
	chunkCoord := world.ChunkForTile(input.Tile)
	chunk, _, err := s.worlds.GetOrCreateChunk(ctx, DefaultWorldID, chunkCoord)
	if err != nil {
		return building.Building{}, err
	}
	tile, ok := findTile(chunk, input.Tile)
	if !ok {
		return building.Building{}, apperror.New(apperror.NotFound, "tile not found")
	}
	placementTiles, err := s.placementTiles(ctx, input.Tile, spec.Footprint)
	if err != nil {
		return building.Building{}, err
	}
	existing, err := s.buildings.ListByPlayer(ctx, input.PlayerID)
	if err != nil {
		return building.Building{}, err
	}
	if err := building.ValidatePlacement(building.PlacementInput{
		Type:             input.Type,
		Tile:             tile,
		Tiles:            placementTiles,
		Footprint:        spec.Footprint,
		Existing:         existing,
		HasTownHall:      building.HasTownHall(existing),
		BuildingLimit:    building.BuildingLimitForTownHall(existing, s.rules),
		UsedLimit:        building.UsedBuildingLimit(existing),
		RequiresTownHall: spec.RequiresTownHall,
	}); err != nil {
		s.log.Warn("building.placement.invalid", "event", "building.placement.invalid", "player_id", input.PlayerID, "building_type", input.Type, "tile_x", input.Tile.X, "tile_y", input.Tile.Y, "error", err.Error())
		return building.Building{}, err
	}
	if err := s.spendCost(ctx, input.PlayerID, spec.Cost, "building:place:"+string(input.Type)); err != nil {
		return building.Building{}, err
	}
	now := s.now()
	var completesAt *time.Time
	state := building.InitialState(spec.BuildDuration)
	if spec.BuildDuration > 0 {
		complete := now.Add(spec.BuildDuration)
		completesAt = &complete
	}
	item := building.Building{
		ID:          building.ID(fmt.Sprintf("b_%d_%s", now.UnixNano(), input.Type)),
		MapID:       DefaultWorldID,
		OwnerID:     string(input.PlayerID),
		Type:        input.Type,
		Name:        spec.Name,
		Level:       spec.Level,
		State:       state,
		Health:      buildingHealth(spec),
		Tile:        input.Tile,
		Footprint:   spec.Footprint,
		StartedAt:   now,
		CompletesAt: completesAt,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
	if err := s.buildings.Create(ctx, item); err != nil {
		s.refundCost(ctx, input.PlayerID, spec.Cost, "building:place:refund:"+string(input.Type))
		return building.Building{}, err
	}
	s.publish(EventBuildingPlaced, item, BuildingPayload{Building: item})
	s.log.Info("building.placed", "event", "building.placed", "building_id", item.ID, "building_type", item.Type, "player_id", item.OwnerID, "tile_x", item.Tile.X, "tile_y", item.Tile.Y, "chunk_id", world.ChunkID(DefaultWorldID, chunkCoord))
	return item, nil
}

func (s *BuildingService) Get(ctx context.Context, id building.ID) (building.Building, error) {
	return s.buildings.FindByID(ctx, id)
}

func (s *BuildingService) ListPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error) {
	return s.buildings.ListByPlayer(ctx, playerID)
}

func (s *BuildingService) ListChunk(ctx context.Context, coord world.ChunkCoord) ([]building.Building, error) {
	return s.buildings.ListByChunk(ctx, DefaultWorldID, coord)
}

func (s *BuildingService) Complete(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	if item.State != building.StateBuilding {
		return item, nil
	}
	now := s.now()
	if item.CompletesAt != nil && item.CompletesAt.After(now) {
		return building.Building{}, apperror.New(apperror.Conflict, "building is still under construction")
	}
	item.State = building.StateActive
	item.CompletesAt = nil
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		return building.Building{}, err
	}
	s.publish(EventBuildingUpdated, item, BuildingPayload{Building: item})
	s.log.Info("building.completed", "event", "building.completed", "building_id", item.ID, "building_type", item.Type, "player_id", playerID)
	return item, nil
}

func (s *BuildingService) Upgrade(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	if item.State != building.StateActive {
		return building.Building{}, apperror.New(apperror.Conflict, "only active buildings can be upgraded")
	}
	next, ok := nextUpgrade(item)
	if !ok {
		return building.Building{}, apperror.New(apperror.Conflict, "building has no available upgrade")
	}
	if err := s.spendCost(ctx, playerID, next.Cost, "building:upgrade:"+string(item.Type)); err != nil {
		return building.Building{}, err
	}
	now := s.now()
	complete := now.Add(next.BuildDuration)
	item.Type = next.Type
	item.Name = next.Name
	item.Level = next.Level
	item.State = building.StateBuilding
	item.Health = buildingHealth(next)
	item.Footprint = next.Footprint
	item.StartedAt = now
	item.CompletesAt = &complete
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		s.refundCost(ctx, playerID, next.Cost, "building:upgrade:refund:"+string(item.Type))
		return building.Building{}, err
	}
	s.publish(EventBuildingUpdated, item, BuildingPayload{Building: item})
	s.log.Info("building.upgraded", "event", "building.upgraded", "building_id", item.ID, "building_type", item.Type, "building_level", item.Level, "player_id", playerID)
	return item, nil
}

func (s *BuildingService) spendCost(ctx context.Context, playerID player.ID, cost []building.Cost, reason string) error {
	if s.economy == nil || len(cost) == 0 {
		return nil
	}
	_, err := s.economy.Spend(ctx, playerID, toEconomyCost(cost), reason)
	return err
}

func (s *BuildingService) refundCost(ctx context.Context, playerID player.ID, cost []building.Cost, reason string) {
	if s.economy == nil || len(cost) == 0 {
		return
	}
	_, _, _ = s.economy.Add(ctx, playerID, toEconomyCost(cost), reason)
}

func toEconomyCost(cost []building.Cost) []economy.ResourceAmount {
	items := make([]economy.ResourceAmount, 0, len(cost))
	for _, item := range cost {
		items = append(items, economy.ResourceAmount{Resource: economy.ResourceType(item.Resource), Amount: item.Amount})
	}
	return items
}

func (s *BuildingService) Demolish(ctx context.Context, id building.ID, playerID player.ID) error {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return err
	}
	if err := s.buildings.Delete(ctx, id); err != nil {
		return err
	}
	s.publish(EventBuildingRemoved, item, BuildingRemovedPayload{BuildingID: item.ID})
	s.log.Info("building.demolished", "event", "building.demolished", "building_id", item.ID, "building_type", item.Type, "player_id", playerID)
	return nil
}

func (s *BuildingService) Cancel(ctx context.Context, id building.ID, playerID player.ID) error {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return err
	}
	if item.State != building.StateBuilding && item.State != building.StatePlanned {
		return apperror.New(apperror.Conflict, "only planned or building objects can be cancelled")
	}
	if err := s.buildings.Delete(ctx, id); err != nil {
		return err
	}
	s.publish(EventBuildingRemoved, item, BuildingRemovedPayload{BuildingID: item.ID})
	s.log.Info("building.cancelled", "event", "building.cancelled", "building_id", item.ID, "building_type", item.Type, "player_id", playerID)
	return nil
}

func (s *BuildingService) Repair(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	if spec, ok := catalog.GetBuilding(item.Type); ok {
		item.Health = buildingHealth(spec)
	} else {
		item.Health = 100
	}
	if item.State == building.StateDamaged {
		item.State = building.StateActive
	}
	item.UpdatedAt = s.now()
	if err := s.buildings.Update(ctx, item); err != nil {
		return building.Building{}, err
	}
	s.publish(EventBuildingUpdated, item, BuildingPayload{Building: item})
	s.log.Info("building.repaired", "event", "building.repaired", "building_id", item.ID, "building_type", item.Type, "player_id", playerID)
	return item, nil
}

func (s *BuildingService) publish(eventType EventType, item building.Building, payload any) {
	if s.events == nil {
		return
	}
	s.events.Publish(Event{
		Type:     eventType,
		ChunkID:  world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)),
		PlayerID: player.ID(item.OwnerID),
		Payload:  payload,
	})
}

func (s *BuildingService) requireOwned(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	item, err := s.buildings.FindByID(ctx, id)
	if err != nil {
		return building.Building{}, err
	}
	if item.OwnerID != string(playerID) {
		return building.Building{}, apperror.New(apperror.Forbidden, "building belongs to another player")
	}
	return item, nil
}

func buildingHealth(spec catalog.BuildingType) int {
	if spec.Health > 0 {
		return spec.Health
	}
	return 100
}

func nextUpgrade(item building.Building) (catalog.BuildingType, bool) {
	spec, ok := catalog.GetBuilding(item.Type)
	if !ok {
		return catalog.BuildingType{}, false
	}
	for _, level := range spec.UpgradeLevels {
		if level.Level == item.Level+1 {
			return catalog.BuildingType{
				Type:          item.Type,
				Name:          spec.Name,
				Level:         level.Level,
				Footprint:     spec.Footprint,
				BuildDuration: level.BuildDuration,
				Population:    level.Population,
				Health:        level.Health,
				Cost:          level.Cost,
			}, true
		}
	}
	for _, level := range spec.UpgradeLevels {
		if level.Level == item.Level && level.NextType != "" {
			return catalog.GetBuilding(level.NextType)
		}
	}
	if len(spec.UpgradeTo) > 0 {
		return catalog.GetBuilding(spec.UpgradeTo[0])
	}
	return catalog.BuildingType{}, false
}

func findTile(chunk world.Chunk, coord world.Coord) (world.Tile, bool) {
	for _, tile := range chunk.Tiles {
		if tile.Coord == coord {
			return tile, true
		}
	}
	return world.Tile{}, false
}

func (s *BuildingService) placementTiles(ctx context.Context, origin world.Coord, footprint building.Footprint) ([]world.Tile, error) {
	coords := placementFootprint(origin, footprint)
	chunks := make(map[world.ChunkCoord]world.Chunk)
	tiles := make([]world.Tile, 0, len(coords))
	for _, coord := range coords {
		chunkCoord := world.ChunkForTile(coord)
		chunk, ok := chunks[chunkCoord]
		if !ok {
			loaded, _, err := s.worlds.GetOrCreateChunk(ctx, DefaultWorldID, chunkCoord)
			if err != nil {
				return nil, err
			}
			chunk = loaded
			chunks[chunkCoord] = loaded
		}
		tile, ok := findTile(chunk, coord)
		if !ok {
			return nil, apperror.New(apperror.NotFound, "tile not found")
		}
		tiles = append(tiles, tile)
	}
	return tiles, nil
}

func placementFootprint(origin world.Coord, footprint building.Footprint) []world.Coord {
	width := max(1, footprint.Width)
	height := max(1, footprint.Height)
	tiles := make([]world.Coord, 0, width*height)
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			tiles = append(tiles, world.Coord{X: origin.X + x, Y: origin.Y + y})
		}
	}
	return tiles
}
