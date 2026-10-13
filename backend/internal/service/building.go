package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/action"
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
	actions   ActionRepository
	monsters  MonsterRepository
}

type PlaceBuildingInput struct {
	PlayerID player.ID
	Type     building.Type
	Tile     world.Coord
}

func NewBuildingService(buildings BuildingRepository, worlds WorldRepository, log *slog.Logger) *BuildingService {
	return &BuildingService{buildings: buildings, worlds: worlds, log: log, now: func() time.Time { return time.Now().UTC() }, rules: building.BuildRules{BaseLimit: 8}}
}

func (s *BuildingService) SetNowForTest(now func() time.Time) {
	s.now = now
}

func (s *BuildingService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *BuildingService) SetEconomy(economyService *EconomyService) {
	s.economy = economyService
}

func (s *BuildingService) SetActionQueue(actions ActionRepository) {
	s.actions = actions
}

func (s *BuildingService) SetMonsters(monsters MonsterRepository) {
	s.monsters = monsters
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
	playerBuildings, err := s.buildings.ListByPlayer(ctx, input.PlayerID)
	if err != nil {
		return building.Building{}, err
	}
	existing, err := s.existingBuildingsForFootprint(ctx, input.Tile, spec.Footprint)
	if err != nil {
		return building.Building{}, err
	}
	if err := building.ValidatePlacement(building.PlacementInput{
		Type:             input.Type,
		Tile:             tile,
		Tiles:            placementTiles,
		Footprint:        spec.Footprint,
		Existing:         existing,
		HasTownHall:      building.HasTownHall(playerBuildings),
		BuildingLimit:    building.BuildingLimitForTownHall(playerBuildings, s.rules),
		UsedLimit:        building.UsedBuildingLimit(playerBuildings),
		RequiresTownHall: spec.RequiresTownHall,
	}); err != nil {
		s.log.Warn("building.placement.invalid", "event", "building.placement.invalid", "player_id", input.PlayerID, "building_type", input.Type, "tile_x", input.Tile.X, "tile_y", input.Tile.Y, "error", err.Error())
		return building.Building{}, err
	}
	if err := s.validateMonsterFree(ctx, input.Tile, spec.Footprint); err != nil {
		return building.Building{}, err
	}
	if err := s.spendCost(ctx, input.PlayerID, spec.Cost, "building:place:"+string(input.Type)); err != nil {
		return building.Building{}, err
	}
	populationReserved := false
	if spec.BuildDuration > 0 && spec.Population > 0 {
		if err := s.reservePopulation(ctx, input.PlayerID, spec.Population, "building:builders:"+string(input.Type)); err != nil {
			s.refundCost(ctx, input.PlayerID, spec.Cost, "building:place:refund:"+string(input.Type))
			return building.Building{}, err
		}
		populationReserved = true
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
		if populationReserved {
			s.releasePopulation(ctx, input.PlayerID, spec.Population, "building:builders:refund:"+string(input.Type))
		}
		return building.Building{}, err
	}
	if item.CompletesAt != nil {
		_ = s.scheduleCompletion(ctx, item)
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

func (s *BuildingService) CompleteDue(ctx context.Context, now time.Time, limit int) (int, error) {
	items, err := s.buildings.ListDue(ctx, now, limit)
	if err != nil {
		return 0, err
	}
	completed := 0
	for _, item := range items {
		if item.State != building.StateBuilding || item.CompletesAt == nil || item.CompletesAt.After(now) {
			continue
		}
		item.State = building.StateActive
		item.CompletesAt = nil
		item.UpdatedAt = now
		if err := s.buildings.Update(ctx, item); err != nil {
			return completed, err
		}
		s.releaseConstructionPopulation(ctx, item, "building:builders:complete:"+string(item.Type))
		s.publish(EventBuildingUpdated, item, BuildingPayload{Building: item})
		s.log.Info("simulation.building.completed", "event", "simulation.building.completed", "building_id", item.ID, "building_type", item.Type, "player_id", item.OwnerID, "chunk_id", world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)))
		completed++
	}
	return completed, nil
}

func (s *BuildingService) Complete(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	return s.CompleteAt(ctx, id, playerID, s.now())
}

func (s *BuildingService) RushComplete(ctx context.Context, id building.ID, playerID player.ID) (building.Building, economy.Inventory, int, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, economy.Inventory{}, 0, err
	}
	if item.State != building.StateBuilding && item.State != building.StatePlanned {
		inventory, invErr := s.currentInventory(ctx, playerID)
		return item, inventory, 0, invErr
	}
	now := s.now()
	remaining := time.Duration(0)
	if item.CompletesAt != nil {
		remaining = item.CompletesAt.Sub(now)
	}
	cost := building.RushCompletionCrystalCost(remaining)
	var inventory economy.Inventory
	if cost > 0 {
		inventory, err = s.economy.Spend(ctx, playerID, []economy.ResourceAmount{{Resource: economy.ResourceAeolianCrystal, Amount: cost}}, "building:rush_complete:"+string(item.Type))
		if err != nil {
			return building.Building{}, economy.Inventory{}, cost, err
		}
	} else {
		inventory, err = s.currentInventory(ctx, playerID)
		if err != nil {
			return building.Building{}, economy.Inventory{}, cost, err
		}
	}
	item.State = building.StateActive
	item.CompletesAt = nil
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		if cost > 0 {
			s.releasePopulation(ctx, playerID, 0, "")
			_, _, _ = s.economy.Add(ctx, playerID, []economy.ResourceAmount{{Resource: economy.ResourceAeolianCrystal, Amount: cost}}, "building:rush_complete:refund:"+string(item.Type))
		}
		return building.Building{}, economy.Inventory{}, cost, err
	}
	s.releaseConstructionPopulation(ctx, item, "building:builders:rush_complete:"+string(item.Type))
	inventory, _ = s.currentInventory(ctx, playerID)
	s.publish(EventBuildingUpdated, item, BuildingPayload{Building: item})
	s.log.Info("building.rush_completed", "event", "building.rush_completed", "building_id", item.ID, "building_type", item.Type, "player_id", playerID, "crystal_cost", cost, "remaining_ms", remaining.Milliseconds())
	return item, inventory, cost, nil
}

func (s *BuildingService) CompleteAt(ctx context.Context, id building.ID, playerID player.ID, now time.Time) (building.Building, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	if item.State != building.StateBuilding {
		return item, nil
	}
	if item.CompletesAt != nil && item.CompletesAt.After(now) {
		return building.Building{}, apperror.New(apperror.Conflict, "building is still under construction")
	}
	item.State = building.StateActive
	item.CompletesAt = nil
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		return building.Building{}, err
	}
	s.releaseConstructionPopulation(ctx, item, "building:builders:complete:"+string(item.Type))
	s.publish(EventBuildingUpdated, item, BuildingPayload{Building: item})
	s.log.Info("building.completed", "event", "building.completed", "building_id", item.ID, "building_type", item.Type, "player_id", playerID)
	return item, nil
}

func (s *BuildingService) currentInventory(ctx context.Context, playerID player.ID) (economy.Inventory, error) {
	if s.economy == nil {
		return economy.Inventory{}, nil
	}
	return s.economy.Inventory(ctx, playerID)
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
	populationReserved := false
	if next.BuildDuration > 0 && next.Population > 0 {
		if err := s.reservePopulation(ctx, playerID, next.Population, "building:builders:upgrade:"+string(item.Type)); err != nil {
			s.refundCost(ctx, playerID, next.Cost, "building:upgrade:refund:"+string(item.Type))
			return building.Building{}, err
		}
		populationReserved = true
	}
	now := s.now()
	var completesAt *time.Time
	state := building.InitialState(next.BuildDuration)
	if next.BuildDuration > 0 {
		complete := now.Add(next.BuildDuration)
		completesAt = &complete
	}
	item.Type = next.Type
	item.Name = next.Name
	item.Level = next.Level
	item.State = state
	item.Health = buildingHealth(next)
	item.Footprint = next.Footprint
	item.StartedAt = now
	item.CompletesAt = completesAt
	item.UpdatedAt = now
	if economy.IsFieldCropBuildingType(string(item.Type)) {
		clearWindleafCycle(&item)
	}
	if err := s.buildings.Update(ctx, item); err != nil {
		s.refundCost(ctx, playerID, next.Cost, "building:upgrade:refund:"+string(item.Type))
		if populationReserved {
			s.releasePopulation(ctx, playerID, next.Population, "building:builders:upgrade:refund:"+string(item.Type))
		}
		return building.Building{}, err
	}
	if item.CompletesAt != nil {
		_ = s.scheduleCompletion(ctx, item)
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

func (s *BuildingService) reservePopulation(ctx context.Context, playerID player.ID, amount int, reason string) error {
	if amount <= 0 || s.economy == nil {
		return nil
	}
	_, err := s.economy.Spend(ctx, playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: amount}}, reason)
	if err != nil {
		return apperror.WithFields(apperror.Conflict, "не хватает свободного населения", map[string]string{"population": fmt.Sprintf("need %d", amount)})
	}
	return nil
}

func (s *BuildingService) releasePopulation(ctx context.Context, playerID player.ID, amount int, reason string) {
	if amount <= 0 || s.economy == nil {
		return
	}
	_, _, _ = s.economy.Add(withoutStarterPopulationBackfill(ctx), playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: amount}}, reason)
}

func (s *BuildingService) releaseConstructionPopulation(ctx context.Context, item building.Building, reason string) {
	s.releasePopulation(ctx, player.ID(item.OwnerID), buildingPopulation(item), reason)
}

func toEconomyCost(cost []building.Cost) []economy.ResourceAmount {
	items := make([]economy.ResourceAmount, 0, len(cost))
	for _, item := range cost {
		items = append(items, economy.ResourceAmount{Resource: economy.ResourceType(item.Resource), Amount: item.Amount})
	}
	return items
}

func (s *BuildingService) existingBuildingsForFootprint(ctx context.Context, origin world.Coord, footprint building.Footprint) ([]building.Building, error) {
	coords := placementFootprint(origin, footprint)
	minX, minY, maxX, maxY := coords[0].X, coords[0].Y, coords[0].X, coords[0].Y
	for _, coord := range coords {
		if coord.X < minX {
			minX = coord.X
		}
		if coord.Y < minY {
			minY = coord.Y
		}
		if coord.X > maxX {
			maxX = coord.X
		}
		if coord.Y > maxY {
			maxY = coord.Y
		}
	}
	return s.buildings.ListByViewport(ctx, DefaultWorldID, minX, minY, maxX, maxY)
}

func (s *BuildingService) validateMonsterFree(ctx context.Context, origin world.Coord, footprint building.Footprint) error {
	if s.monsters == nil {
		return nil
	}
	coords := placementFootprint(origin, footprint)
	minX, minY, maxX, maxY := coords[0].X, coords[0].Y, coords[0].X, coords[0].Y
	occupied := make(map[world.Coord]bool, len(coords))
	for _, coord := range coords {
		occupied[coord] = true
		if coord.X < minX {
			minX = coord.X
		}
		if coord.Y < minY {
			minY = coord.Y
		}
		if coord.X > maxX {
			maxX = coord.X
		}
		if coord.Y > maxY {
			maxY = coord.Y
		}
	}
	monsters, err := s.monsters.ListByViewport(ctx, DefaultWorldID, minX, minY, maxX, maxY)
	if err != nil {
		return err
	}
	for _, monster := range monsters {
		if occupied[monster.Tile] {
			return apperror.WithFields(apperror.Conflict, "на клетке находится монстр", map[string]string{"tile": fmt.Sprintf("%d:%d", monster.Tile.X, monster.Tile.Y), "monster_id": string(monster.ID)})
		}
	}
	return nil
}

func buildingPopulation(item building.Building) int {
	spec, ok := catalog.GetBuilding(item.Type)
	if !ok {
		return 0
	}
	for _, level := range spec.UpgradeLevels {
		if level.Level == item.Level {
			return level.Population
		}
	}
	return spec.Population
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
	s.releaseConstructionPopulation(ctx, item, "building:builders:cancel:"+string(item.Type))
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

func (s *BuildingService) scheduleCompletion(ctx context.Context, item building.Building) error {
	if s.actions == nil || item.CompletesAt == nil {
		return nil
	}
	now := s.now()
	return s.actions.Append(ctx, action.NewGameAction(
		action.ID(fmt.Sprintf("act_building_%s_%d", item.ID, item.CompletesAt.UnixNano())),
		action.TypeCompleteBuilding,
		fmt.Sprintf("building:%s:complete:%d", item.ID, item.CompletesAt.UnixNano()),
		action.ObjectRef{ID: item.OwnerID, Type: "player"},
		action.ObjectRef{ID: string(item.ID), Type: "building"},
		*item.CompletesAt,
		now,
	))
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

func clearWindleafCycle(item *building.Building) {
	item.FieldStage = 0
	item.FieldStageStartedAt = nil
	item.FieldStageReadyAt = nil
	item.FieldSuperCrop = false
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
