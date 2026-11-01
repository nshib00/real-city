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
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

type BuildingService struct {
	allianceBenefits *AllianceService
	buildings        BuildingRepository
	worlds           WorldRepository
	log              *slog.Logger
	now              func() time.Time
	rules            building.BuildRules
	events           *EventBus
	economy          *EconomyService
	actions          ActionRepository
	monsters         MonsterRepository
	experience       *ExperienceService
	resources        *ResourceService
	repairUOW        UnitOfWork
	pvpProtection    PvPProtectionRepository
}

type PlaceBuildingInput struct {
	PlayerID player.ID
	Type     building.Type
	Tile     world.Coord
}

func NewBuildingService(buildings BuildingRepository, worlds WorldRepository, log *slog.Logger) *BuildingService {
	catalog.ValidateBuildingXP()
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

func (s *BuildingService) SetExperience(experience *ExperienceService) {
	s.experience = experience
}

func (s *BuildingService) SetResources(resources *ResourceService) { s.resources = resources }

func (s *BuildingService) Catalog(ctx context.Context) ([]catalog.BuildingType, error) {
	_ = ctx
	return catalog.FirstLevelBuildings(), nil
}

func (s *BuildingService) FullCatalog(ctx context.Context) ([]catalog.BuildingType, error) {
	_ = ctx
	return catalog.AllBuildings(), nil
}

func (s *BuildingService) place(ctx context.Context, input PlaceBuildingInput) (placed building.Building, resultErr error) {
	input.Tile = world.NormalizeCoord(input.Tile)
	totalStarted := time.Now()
	defer func() { observability.ObservePlacement("total", totalStarted, resultErr) }()
	spec, ok := catalog.GetBuilding(input.Type)
	if !ok {
		return building.Building{}, apperror.WithFields(apperror.Validation, "unknown building type", map[string]string{"type": string(input.Type)})
	}
	if input.Type == building.TypeStoneHouse {
		return building.Building{}, apperror.New(apperror.Conflict, "stone house requires wooden house level 6 upgrade")
	}
	if _, isRuin := catalog.RuinSpecs[input.Type]; !isRuin && !catalog.CanPlaceDirectly(input.Type) {
		return building.Building{}, apperror.New(apperror.Conflict, "building requires an upgrade from its previous type")
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
	criticalStarted := time.Now()
	defer func() { observability.ObservePlacement("critical", criticalStarted, resultErr) }()
	playerStats, err := s.buildings.PlayerPlacementStats(ctx, input.PlayerID)
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
		HasTownHall:      playerStats.HasTownHall,
		BuildingLimit:    s.rules.LimitForTownHallLevel(playerStats.TownHallLevel),
		UsedLimit:        playerStats.UsedLimit,
		RequiresTownHall: spec.RequiresTownHall,
	}); err != nil {
		s.log.Warn("building.placement.invalid", "event", "building.placement.invalid", "player_id", input.PlayerID, "building_type", input.Type, "tile_x", input.Tile.X, "tile_y", input.Tile.Y, "error", err.Error())
		return building.Building{}, err
	}
	if err := s.validateMonsterFree(ctx, input.Tile, spec.Footprint); err != nil {
		return building.Building{}, err
	}
	if input.Type == building.TypeOilWell && s.resources != nil {
		if err := s.resources.CheckOilAvailable(ctx, input.Tile); err != nil {
			return building.Building{}, err
		}
	}
	duration, err := s.buffedDuration(ctx, input.PlayerID, spec.BuildDuration, "build_speed")
	if err != nil {
		return building.Building{}, err
	}
	spec.BuildDuration = duration
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
	if building.IsTrapType(item.Type) {
		item.TrapCharges = 3
		if item.Type == building.TypeDefenseResinSnare {
			item.TrapCharges = 2
		}
	}
	if err := s.buildings.Create(ctx, item); err != nil {
		s.refundCost(ctx, input.PlayerID, spec.Cost, "building:place:refund:"+string(input.Type))
		if populationReserved {
			_ = s.releasePopulation(ctx, input.PlayerID, spec.Population, "building:builders:refund:"+string(input.Type))
		}
		return building.Building{}, err
	}
	if item.Type == building.TypeOilWell && s.resources != nil {
		if err := s.resources.ClaimOilWell(ctx, item); err != nil {
			_ = s.buildings.Delete(ctx, item.ID)
			s.refundCost(ctx, input.PlayerID, spec.Cost, "building:place:refund:"+string(input.Type))
			if populationReserved {
				_ = s.releasePopulation(ctx, input.PlayerID, spec.Population, "building:builders:refund:"+string(input.Type))
			}
			return building.Building{}, err
		}
	}
	if item.CompletesAt != nil {
		if err := s.scheduleCompletion(ctx, item); err != nil {
			return building.Building{}, err
		}
	} else if err := s.awardCompletionXP(ctx, item); err != nil {
		return building.Building{}, err
	}
	s.publish(ctx, EventBuildingPlaced, item, BuildingPayload{Building: item, Reason: "placed"})
	s.log.Info("building.placed", "event", "building.placed", "building_id", item.ID, "building_type", item.Type, "player_id", item.OwnerID, "tile_x", item.Tile.X, "tile_y", item.Tile.Y, "chunk_id", world.ChunkID(DefaultWorldID, chunkCoord))
	return item, nil
}

func (s *BuildingService) Get(ctx context.Context, id building.ID) (building.Building, error) {
	return s.buildings.FindByID(ctx, id)
}

func (s *BuildingService) ListPlayer(ctx context.Context, playerID player.ID) ([]building.Building, error) {
	return s.buildings.ListByPlayer(ctx, playerID)
}

func (s *BuildingService) ListNearby(ctx context.Context, center world.ChunkCoord, radius int) ([]building.Building, error) {
	if radius < 0 || radius > MaxChunkRadius {
		return nil, apperror.WithFields(apperror.Validation, "invalid chunk radius", map[string]string{"radius": "must be between 0 and 3"})
	}
	xRanges := nearbyChunkRanges(center.X, radius)
	yRanges := nearbyChunkRanges(center.Y, radius)
	items := make([]building.Building, 0)
	seen := make(map[building.ID]bool)
	for _, yRange := range yRanges {
		for _, xRange := range xRanges {
			found, err := s.buildings.ListByViewport(ctx, DefaultWorldID,
				xRange[0]*world.ChunkSize, yRange[0]*world.ChunkSize,
				(xRange[1]+1)*world.ChunkSize-1, (yRange[1]+1)*world.ChunkSize-1)
			if err != nil {
				return nil, err
			}
			for _, item := range found {
				if !seen[item.ID] {
					seen[item.ID] = true
					items = append(items, item)
				}
			}
		}
	}
	return items, nil
}

func nearbyChunkRanges(center, radius int) [][2]int {
	worldChunks := worldgen.WorldSizeTiles / world.ChunkSize
	visible := make([]bool, worldChunks)
	for offset := -radius; offset <= radius; offset++ {
		chunk := ((center+offset)%worldChunks + worldChunks) % worldChunks
		visible[chunk] = true
	}
	ranges := make([][2]int, 0, 2)
	for start := 0; start < worldChunks; {
		if !visible[start] {
			start++
			continue
		}
		end := start
		for end+1 < worldChunks && visible[end+1] {
			end++
		}
		ranges = append(ranges, [2]int{start, end})
		start = end + 1
	}
	return ranges
}

func (s *BuildingService) ListChunk(ctx context.Context, coord world.ChunkCoord) ([]building.Building, error) {
	return s.buildings.ListByChunk(ctx, DefaultWorldID, coord)
}

func (s *BuildingService) CompleteDue(ctx context.Context, now time.Time, limit int) (int, error) {
	if err := s.cleanupRuinedRuins(ctx); err != nil {
		return 0, err
	}
	items, err := s.buildings.ListDue(ctx, now, limit)
	if err != nil {
		return 0, err
	}
	completed := 0
	for _, item := range items {
		if item.State != building.StateBuilding || item.CompletesAt == nil || item.CompletesAt.After(now) {
			continue
		}
		if _, err := s.CompleteAt(ctx, item.ID, player.ID(item.OwnerID), now); err != nil {
			if isNotFound(err) {
				continue
			}
			return completed, err
		}
		completed++
	}
	return completed, nil
}

func (s *BuildingService) cleanupRuinedRuins(ctx context.Context) error {
	items, err := s.buildings.ListRuinedRuins(ctx, 100)
	if err != nil {
		return err
	}
	for _, item := range items {
		if !catalog.IsRuin(item.Type) {
			continue
		}
		if err := s.buildings.Delete(ctx, item.ID); err != nil {
			return err
		}
		s.publish(ctx, EventBuildingRemoved, item, BuildingRemovedPayload{BuildingID: item.ID, Reason: "destroyed"})
	}
	return nil
}

func (s *BuildingService) Complete(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	return s.CompleteAt(ctx, id, playerID, s.now())
}

func (s *BuildingService) rushComplete(ctx context.Context, id building.ID, playerID player.ID) (building.Building, economy.Inventory, int, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, economy.Inventory{}, 0, err
	}
	if item.State != building.StateBuilding && item.State != building.StatePlanned {
		inventory, invErr := s.currentInventory(ctx, playerID)
		return item, inventory, 0, invErr
	}
	reservedBuilders := item.State == building.StateBuilding && item.CompletesAt != nil
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
			_, _, _ = s.economy.Add(ctx, playerID, []economy.ResourceAmount{{Resource: economy.ResourceAeolianCrystal, Amount: cost}}, "building:rush_complete:refund:"+string(item.Type))
		}
		return building.Building{}, economy.Inventory{}, cost, err
	}
	if reservedBuilders {
		if err := s.releaseConstructionPopulation(ctx, item, "building:builders:rush_complete:"+string(item.Type)); err != nil {
			return building.Building{}, economy.Inventory{}, cost, err
		}
	}
	if err := s.awardCompletionXP(ctx, item); err != nil {
		return building.Building{}, economy.Inventory{}, cost, err
	}
	inventory, _ = s.currentInventory(ctx, playerID)
	s.log.Info("building.rush_completed", "event", "building.rush_completed", "building_id", item.ID, "building_type", item.Type, "player_id", playerID, "crystal_cost", cost, "remaining_ms", remaining.Milliseconds())
	s.publish(ctx, EventBuildingUpdated, item, BuildingPayload{Building: item, Reason: "rushed"})
	return item, inventory, cost, nil
}

func (s *BuildingService) completeAt(ctx context.Context, id building.ID, playerID player.ID, now time.Time) (building.Building, error) {
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
	reservedBuilders := item.CompletesAt != nil
	item.State = building.StateActive
	item.CompletesAt = nil
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		return building.Building{}, err
	}
	if reservedBuilders {
		if err := s.releaseConstructionPopulation(ctx, item, "building:builders:complete:"+string(item.Type)); err != nil {
			return building.Building{}, err
		}
	}
	if err := s.awardCompletionXP(ctx, item); err != nil {
		return building.Building{}, err
	}
	s.log.Info("building.completed", "event", "building.completed", "building_id", item.ID, "building_type", item.Type, "player_id", playerID)
	s.publish(ctx, EventBuildingUpdated, item, BuildingPayload{Building: item, Reason: completionReason(item)})
	return item, nil
}

func (s *BuildingService) currentInventory(ctx context.Context, playerID player.ID) (economy.Inventory, error) {
	if s.economy == nil {
		return economy.Inventory{}, nil
	}
	return s.economy.Inventory(ctx, playerID)
}

func (s *BuildingService) Upgrade(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	return s.UpgradeTo(ctx, id, playerID, "")
}

func (s *BuildingService) upgradeTo(ctx context.Context, id building.ID, playerID player.ID, targetType building.Type) (building.Building, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	if item.State != building.StateActive {
		return building.Building{}, apperror.New(apperror.Conflict, "only active buildings can be upgraded")
	}
	if err := s.requireIdleBuilding(ctx, item); err != nil {
		return building.Building{}, err
	}
	next, ok := nextUpgradeTo(item, targetType)
	if !ok {
		return building.Building{}, apperror.New(apperror.Validation, "building has no available upgrade for selected target")
	}
	duration, err := s.buffedDuration(ctx, playerID, next.BuildDuration, "build_speed")
	if err != nil {
		return building.Building{}, err
	}
	next.BuildDuration = duration
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
	if item.Rotation%2 == 1 {
		item.Footprint.Width, item.Footprint.Height = item.Footprint.Height, item.Footprint.Width
	}
	item.StartedAt = now
	item.CompletesAt = completesAt
	item.UpdatedAt = now
	if economy.IsFieldCropBuildingType(string(item.Type)) {
		clearWindleafCycle(&item)
	}
	if err := s.buildings.Update(ctx, item); err != nil {
		s.refundCost(ctx, playerID, next.Cost, "building:upgrade:refund:"+string(item.Type))
		if populationReserved {
			_ = s.releasePopulation(ctx, playerID, next.Population, "building:builders:upgrade:refund:"+string(item.Type))
		}
		return building.Building{}, err
	}
	if item.CompletesAt != nil {
		if err := s.scheduleCompletion(ctx, item); err != nil {
			return building.Building{}, err
		}
	} else if err := s.awardCompletionXP(ctx, item); err != nil {
		return building.Building{}, err
	}
	s.log.Info("building.upgraded", "event", "building.upgraded", "building_id", item.ID, "building_type", item.Type, "building_level", item.Level, "player_id", playerID)
	reason := "upgrade_started"
	if item.CompletesAt == nil {
		reason = "upgrade_completed"
	}
	s.publish(ctx, EventBuildingUpdated, item, BuildingPayload{Building: item, Reason: reason})
	return item, nil
}

func (s *BuildingService) setCannonEnabled(ctx context.Context, id building.ID, playerID player.ID, enabled bool) (building.Building, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	if !catalog.IsDefenseWeapon(item.Type) {
		return building.Building{}, apperror.New(apperror.Validation, "building is not a defense weapon")
	}
	if item.CannonEnabled == enabled {
		return item, nil
	}
	if enabled {
		if (item.State != building.StateActive && item.State != building.StateDamaged) || item.Health <= 0 {
			return building.Building{}, apperror.New(apperror.Conflict, "defense weapon must be active")
		}
		if err := s.reservePopulation(ctx, playerID, 1, "cannon:garrison:"+string(id)); err != nil {
			return building.Building{}, err
		}
	}
	item.CannonEnabled = enabled
	if !enabled {
		item.CannonTargetID = ""
	}
	item.UpdatedAt = s.now()
	if err := s.buildings.Update(ctx, item); err != nil {
		if enabled {
			_ = s.releasePopulation(ctx, playerID, 1, "cannon:garrison:refund:"+string(id))
		}
		return building.Building{}, err
	}
	if !enabled {
		if err := s.releasePopulation(ctx, playerID, 1, "cannon:garrison:release:"+string(id)); err != nil {
			return building.Building{}, err
		}
	}
	s.publish(ctx, EventBuildingUpdated, item, BuildingPayload{Building: item})
	return item, nil
}

func (s *BuildingService) reloadTrap(ctx context.Context, id building.ID, playerID player.ID) (building.Building, error) {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	stats, ok := catalog.DefenseTrapLevel(item.Type, item.Level)
	if !ok {
		return building.Building{}, apperror.New(apperror.Validation, "building is not a trap")
	}
	if item.State != building.StateActive && item.State != building.StateDamaged {
		return building.Building{}, apperror.New(apperror.Conflict, "trap must be active")
	}
	if item.TrapCharges >= stats.MaxCharges {
		return item, nil
	}
	if err := s.spendCost(ctx, playerID, stats.Reload, "trap:reload:"+string(id)); err != nil {
		return building.Building{}, err
	}
	item.TrapCharges = stats.MaxCharges
	item.UpdatedAt = s.now()
	if err := s.buildings.Update(ctx, item); err != nil {
		s.refundCost(ctx, playerID, stats.Reload, "trap:reload:refund:"+string(id))
		return building.Building{}, err
	}
	s.publish(ctx, EventBuildingUpdated, item, BuildingPayload{Building: item})
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

func (s *BuildingService) releasePopulation(ctx context.Context, playerID player.ID, amount int, reason string) error {
	if amount <= 0 || s.economy == nil {
		return nil
	}
	_, _, err := s.economy.Add(withoutStarterPopulationBackfill(ctx), playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: amount}}, reason)
	return err
}

func (s *BuildingService) releaseConstructionPopulation(ctx context.Context, item building.Building, reason string) error {
	return s.releasePopulation(ctx, player.ID(item.OwnerID), buildingPopulation(item), reason)
}

func toEconomyCost(cost []building.Cost) []economy.ResourceAmount {
	items := make([]economy.ResourceAmount, 0, len(cost))
	for _, item := range cost {
		items = append(items, economy.ResourceAmount{Resource: economy.ResourceType(item.Resource), Amount: item.Amount})
	}
	return items
}

func (s *BuildingService) existingBuildingsForFootprint(ctx context.Context, origin world.Coord, footprint building.Footprint) ([]building.Building, error) {
	origin = world.NormalizeCoord(origin)
	items := []building.Building{}
	seen := map[building.ID]bool{}
	// Include mirrored rectangles to find footprints that straddle either seam.
	for _, dx := range []int{-world.WorldSize, 0, world.WorldSize} {
		for _, dy := range []int{-world.WorldSize, 0, world.WorldSize} {
			found, err := s.buildings.ListIntersectingFootprint(ctx, DefaultWorldID, origin.X+dx, origin.Y+dy, origin.X+dx+max(1, footprint.Width)-1, origin.Y+dy+max(1, footprint.Height)-1)
			if err != nil {
				return nil, err
			}
			for _, b := range found {
				if !seen[b.ID] {
					seen[b.ID] = true
					items = append(items, b)
				}
			}
		}
	}
	return items, nil
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

func (s *BuildingService) demolish(ctx context.Context, id building.ID, playerID player.ID) error {
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return err
	}
	if catalog.IsRuin(item.Type) && item.State == building.StateRuined {
		return apperror.New(apperror.Conflict, "разрушенная руина больше не принадлежит игроку")
	}
	if s.economy != nil {
		if _, err := s.economy.Inventory(ctx, playerID); err != nil {
			return err
		}
		item, err = s.requireOwned(ctx, id, playerID)
		if err != nil {
			return err
		}
		if catalog.IsRuin(item.Type) && item.State == building.StateRuined {
			return apperror.New(apperror.Conflict, "разрушенная руина больше не принадлежит игроку")
		}
	}
	releasedPopulation := 0
	if item.State == building.StateBuilding && item.CompletesAt != nil {
		releasedPopulation += buildingPopulation(item)
	}
	if item.FieldStageStartedAt != nil {
		releasedPopulation += buildingPopulation(item)
	}
	if catalog.IsDefenseWeapon(item.Type) && item.CannonEnabled {
		releasedPopulation++
	}
	if s.economy != nil && s.economy.repo != nil {
		jobs, err := s.economy.repo.ListProductionJobs(ctx, playerID)
		if err != nil {
			return err
		}
		for _, job := range jobs {
			if job.BuildingID != string(id) || (job.State != economy.ProductionRunning && job.State != economy.ProductionReady) {
				continue
			}
			if job.State == economy.ProductionRunning {
				recipe, ok := catalog.RecipeForBuildingLevel(job.RecipeID, item.Level)
				if !ok {
					return apperror.New(apperror.Conflict, "production recipe not found")
				}
				releasedPopulation += recipe.Workers
			}
			job.State = economy.ProductionCancelled
			job.UpdatedAt = s.now()
			if err := s.economy.repo.SaveProductionJob(ctx, job); err != nil {
				return err
			}
		}
	}
	refundCoins := catalog.DemolitionRefundCoins(item.Type, item.Level)
	if err := s.buildings.Delete(ctx, id); err != nil {
		return err
	}
	if item.Type == building.TypeOilWell && s.resources != nil {
		if err := s.resources.ReleaseOilWell(ctx, item.Tile, item.OwnerID); err != nil {
			return err
		}
	}
	if s.economy != nil && (releasedPopulation > 0 || refundCoins > 0) {
		items := make([]economy.ResourceAmount, 0, 2)
		if releasedPopulation > 0 {
			items = append(items, economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: releasedPopulation})
		}
		if refundCoins > 0 {
			items = append(items, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: refundCoins})
		}
		if _, _, err := s.economy.Add(withUncappedCoins(withoutStarterPopulationBackfill(ctx)), playerID, items, "building:demolish:"+string(item.ID)); err != nil {
			return err
		}
	}
	s.log.Info("building.demolished", "event", "building.demolished", "building_id", item.ID, "building_type", item.Type, "player_id", playerID, "refund_coins", refundCoins, "population_returned", releasedPopulation)
	s.publish(ctx, EventBuildingRemoved, item, BuildingRemovedPayload{BuildingID: item.ID, Reason: "demolished"})
	return nil
}

func (s *BuildingService) awardCompletionXP(ctx context.Context, item building.Building) error {
	if s.experience == nil {
		return nil
	}
	reward := catalog.ExperienceForBuilding(item.Type, item.Level).Completion
	key := fmt.Sprintf("building:%s:%s:%d:complete", item.ID, item.Type, item.Level)
	// The free, instant starting hall must not become an unlimited XP loop.
	if item.Type == building.TypeTownHall && item.Level == 1 {
		key = fmt.Sprintf("player:%s:town_hall:first_complete", item.OwnerID)
	}
	return s.experience.Award(ctx, player.ID(item.OwnerID), reward, "building:complete", key)
}

func (s *BuildingService) requireIdleBuilding(ctx context.Context, item building.Building) error {
	if item.FieldStage > 0 {
		return apperror.New(apperror.Conflict, "завершите цикл выращивания перед изменением поля")
	}
	if s.economy == nil || s.economy.repo == nil {
		return nil
	}
	jobs, err := s.economy.repo.ListProductionJobs(ctx, player.ID(item.OwnerID))
	if err != nil {
		return err
	}
	for _, job := range jobs {
		if job.BuildingID == string(item.ID) && (job.State == economy.ProductionRunning || job.State == economy.ProductionReady) {
			return apperror.New(apperror.Conflict, "завершите производство перед изменением постройки")
		}
	}
	return nil
}

func (s *BuildingService) cancel(ctx context.Context, id building.ID, playerID player.ID) error {
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
	if item.Type == building.TypeOilWell && s.resources != nil {
		if err := s.resources.ReleaseOilWell(ctx, item.Tile, item.OwnerID); err != nil {
			return err
		}
	}
	if item.State == building.StateBuilding && item.CompletesAt != nil {
		if err := s.releaseConstructionPopulation(ctx, item, "building:builders:cancel:"+string(item.Type)); err != nil {
			return err
		}
	}
	if catalog.IsDefenseWeapon(item.Type) && item.CannonEnabled {
		if err := s.releasePopulation(ctx, playerID, 1, "cannon:garrison:cancel:"+string(item.ID)); err != nil {
			return err
		}
	}
	s.log.Info("building.cancelled", "event", "building.cancelled", "building_id", item.ID, "building_type", item.Type, "player_id", playerID)
	s.publish(ctx, EventBuildingRemoved, item, BuildingRemovedPayload{BuildingID: item.ID, Reason: "cancelled"})
	return nil
}

func buildingHealthForLevel(kind building.Type, level int) int {
	spec, ok := catalog.GetBuilding(kind)
	if !ok {
		return 100
	}
	for _, upgrade := range spec.UpgradeLevels {
		if upgrade.Level == level && upgrade.Health > 0 {
			return upgrade.Health
		}
	}
	return buildingHealth(spec)
}

func (s *BuildingService) relocate(ctx context.Context, id building.ID, playerID player.ID, destination world.Coord, rotation int) (building.Building, error) {
	destination = world.NormalizeCoord(destination)
	item, err := s.requireOwned(ctx, id, playerID)
	if err != nil {
		return building.Building{}, err
	}
	if (item.Type == building.TypeOilWell || catalog.IsRuin(item.Type)) && item.Tile != destination {
		return building.Building{}, apperror.New(apperror.Conflict, "эту постройку нельзя перенести с исходной клетки")
	}
	if rotation < 0 || rotation > 3 {
		return building.Building{}, apperror.WithFields(apperror.Validation, "недопустимый поворот", map[string]string{"rotation": "допустимы значения 0–3"})
	}
	if item.State != building.StateActive && item.State != building.StateDamaged {
		return building.Building{}, apperror.New(apperror.Conflict, "перемещать и поворачивать можно только завершённые постройки")
	}
	if item.Tile == destination && item.Rotation == rotation {
		return item, nil
	}
	if err := s.requireIdleBuilding(ctx, item); err != nil {
		return building.Building{}, err
	}
	width, height := item.Footprint.Width, item.Footprint.Height
	if (rotation-item.Rotation+4)%2 == 1 {
		width, height = height, width
	}
	footprint := building.Footprint{Width: width, Height: height}
	tiles, err := s.placementTiles(ctx, destination, footprint)
	if err != nil {
		return building.Building{}, err
	}
	existing, err := s.existingBuildingsForFootprint(ctx, destination, footprint)
	if err != nil {
		return building.Building{}, err
	}
	others := make([]building.Building, 0, len(existing))
	for _, other := range existing {
		if other.ID != item.ID {
			others = append(others, other)
		}
	}
	if err := building.ValidatePlacement(building.PlacementInput{
		Type: item.Type, Tile: tiles[0], Tiles: tiles, Footprint: footprint,
		Existing: others, HasTownHall: item.Type != building.TypeTownHall,
		BuildingLimit: 1, UsedLimit: 0, RequiresTownHall: false,
	}); err != nil {
		return building.Building{}, err
	}
	if err := s.validateMonsterFree(ctx, destination, footprint); err != nil {
		return building.Building{}, err
	}
	previous := item
	item.Tile = destination
	item.Footprint = footprint
	item.Rotation = rotation
	item.UpdatedAt = s.now()
	changed, err := s.buildings.RelocateIfCurrent(ctx, previous, item)
	if err != nil {
		return building.Building{}, err
	}
	if !changed {
		return building.Building{}, apperror.New(apperror.Conflict, "постройка или целевые клетки изменились; попробуйте ещё раз")
	}
	if s.events != nil && previous.Tile != item.Tile && world.ChunkForTile(previous.Tile) != world.ChunkForTile(item.Tile) {
		publishEvent(ctx, s.events, Event{Type: EventBuildingRemoved, ChunkID: world.ChunkID(previous.MapID, world.ChunkForTile(previous.Tile)), PlayerID: playerID,
			Payload: BuildingRemovedPayload{BuildingID: item.ID, Reason: "moved"}})
	}
	s.publish(ctx, EventBuildingUpdated, item, BuildingPayload{Building: item, Reason: "relocated"})
	return item, nil
}

func (s *BuildingService) publish(ctx context.Context, eventType EventType, item building.Building, payload any) {
	if s.events == nil {
		return
	}
	publishEvent(ctx, s.events, Event{
		Type:     eventType,
		ChunkID:  world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)),
		PlayerID: player.ID(item.OwnerID),
		Payload:  payload,
	})
}

func completionReason(item building.Building) string {
	if item.StartedAt.After(item.CreatedAt) {
		return "upgrade_completed"
	}
	return "completed"
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
	return nextUpgradeTo(item, "")
}

func nextUpgradeTo(item building.Building, targetType building.Type) (catalog.BuildingType, bool) {
	spec, ok := catalog.GetBuilding(item.Type)
	if !ok {
		return catalog.BuildingType{}, false
	}
	for _, level := range spec.UpgradeLevels {
		if level.Level == item.Level+1 {
			if targetType != "" && targetType != item.Type {
				return catalog.BuildingType{}, false
			}
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
			if targetType != "" && targetType != level.NextType {
				return catalog.BuildingType{}, false
			}
			return catalog.GetBuilding(level.NextType)
		}
	}
	if len(spec.UpgradeTo) > 0 {
		if targetType == "" {
			if len(spec.UpgradeTo) != 1 {
				return catalog.BuildingType{}, false
			}
			targetType = spec.UpgradeTo[0]
		}
		for _, allowed := range spec.UpgradeTo {
			if allowed == targetType {
				return catalog.GetBuilding(targetType)
			}
		}
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
			tiles = append(tiles, world.NormalizeCoord(world.Coord{X: origin.X + x, Y: origin.Y + y}))
		}
	}
	return tiles
}

func (s *BuildingService) SetAllianceBenefits(alliances *AllianceService) {
	s.allianceBenefits = alliances
}
func (s *BuildingService) buffedDuration(ctx context.Context, p player.ID, d time.Duration, effect string) (time.Duration, error) {
	if s.allianceBenefits == nil || d <= 0 {
		return d, nil
	}
	percent, err := s.allianceBenefits.Percent(ctx, p, effect)
	if err != nil {
		return 0, err
	}
	return max(time.Second, d*time.Duration(100-percent)/100), nil
}
func (s *BuildingService) ProtectedDamage(ctx context.Context, p player.ID, damage int) (int, error) {
	if s.allianceBenefits == nil || damage <= 0 {
		return damage, nil
	}
	percent, err := s.allianceBenefits.Percent(ctx, p, "defense")
	if err != nil {
		return 0, err
	}
	return max(1, damage*(100-percent)/100), nil
}
