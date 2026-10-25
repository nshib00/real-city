package service

import (
	"context"
	"fmt"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

func oilExtractionForLevel(level int) (time.Duration, int, int) {
	recipe := catalog.OilExtractionRecipe(level)
	return recipe.Duration, recipe.Output[0].Amount, catalog.OilExtractionDepletion(level)
}

func (s *ResourceService) oilNodeAt(ctx context.Context, coord world.Coord) (economy.ResourceNode, bool, error) {
	nodes, err := s.repo.ListResourceNodes(ctx, DefaultWorldID)
	if err != nil {
		return economy.ResourceNode{}, false, err
	}
	for _, node := range nodes {
		if node.Resource == economy.ResourceOil && node.Tile == coord {
			return node, true, nil
		}
	}
	return economy.ResourceNode{}, false, nil
}

func (s *ResourceService) CheckOilAvailable(ctx context.Context, coord world.Coord) error {
	node, found, err := s.oilNodeAt(ctx, coord)
	if err != nil {
		return err
	}
	if found && (node.OwnerID != "" || node.Amount <= 0 || node.State == economy.NodeDepleted) {
		return apperror.New(apperror.Conflict, "месторождение уже занято или истощено")
	}
	return nil
}

func (s *ResourceService) ClaimOilWell(ctx context.Context, well building.Building) error {
	if err := s.CheckOilAvailable(ctx, well.Tile); err != nil {
		return err
	}
	node, found, err := s.oilNodeAt(ctx, well.Tile)
	if err != nil {
		return err
	}
	if !found {
		amount := 100000
		node = economy.OilWellNode(economy.NodeID(fmt.Sprintf("node_oil_%d_%d_%d", well.Tile.X, well.Tile.Y, s.now().UnixNano())), well.MapID, well.Tile.X, well.Tile.Y, amount)
		node.CreatedAt = s.now()
	}
	node.OwnerID = well.OwnerID
	node.State = economy.NodeClaimed
	node.UpdatedAt = s.now()
	if err := s.repo.SaveResourceNode(ctx, node); err != nil {
		return err
	}
	s.publish(node)
	return nil
}

func (s *ResourceService) ReleaseOilWell(ctx context.Context, coord world.Coord, ownerID string) error {
	node, found, err := s.oilNodeAt(ctx, coord)
	if err != nil {
		return err
	}
	if !found || node.OwnerID != ownerID || node.State == economy.NodeDepleted {
		return nil
	}
	node.OwnerID = ""
	node.State = economy.NodeNeutral
	node.UpdatedAt = s.now()
	if err := s.repo.SaveResourceNode(ctx, node); err != nil {
		return err
	}
	s.publish(node)
	return nil
}

func (s *ResourceService) CancelOilJobs(ctx context.Context, well building.Building) error {
	if well.CompletesAt != nil {
		workers := buildingPopulation(well)
		if workers > 0 {
			if _, _, err := s.economy.Add(ctx, player.ID(well.OwnerID), []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: workers}}, "oil:construction_destroyed:"+string(well.ID)); err != nil {
				return err
			}
		}
	}
	jobs, err := s.repo.ListProductionJobs(ctx, player.ID(well.OwnerID))
	if err != nil {
		return err
	}
	for _, job := range jobs {
		if job.BuildingID != string(well.ID) || job.RecipeID != catalog.OilExtractionRecipeID || (job.State != economy.ProductionRunning && job.State != economy.ProductionReady) {
			continue
		}
		if job.State == economy.ProductionRunning {
			workers := catalog.OilExtractionRecipe(well.Level).Workers
			if _, _, err := s.economy.Add(ctx, player.ID(well.OwnerID), []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: workers}}, "oil:workers:destroyed:"+string(job.ID)); err != nil {
				return err
			}
		}
		job.State = economy.ProductionCancelled
		job.UpdatedAt = s.now()
		if err := s.repo.SaveProductionJob(ctx, job); err != nil {
			return err
		}
	}
	return nil
}

func (s *ResourceService) tickOil(ctx context.Context, node economy.ResourceNode, now time.Time) (bool, error) {
	if node.State == economy.NodeDepleted {
		if node.OwnerID != "" {
			items, err := s.buildings.ListIntersectingFootprint(ctx, node.MapID, node.Tile.X, node.Tile.Y, node.Tile.X, node.Tile.Y)
			if err != nil {
				return false, err
			}
			for _, item := range items {
				if item.Type == building.TypeOilWell && item.Tile == node.Tile && item.OwnerID == node.OwnerID {
					if err := s.buildings.Delete(ctx, item.ID); err != nil {
						return false, err
					}
					if s.events != nil {
						s.events.Publish(Event{Type: EventBuildingRemoved, ChunkID: world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)), Payload: BuildingRemovedPayload{BuildingID: item.ID, Reason: "oil_depleted"}})
					}
				}
			}
			if err := s.changeOilTerrain(ctx, node.Tile, world.TerrainGrass, "oil_depleted"); err != nil {
				return false, err
			}
			node.OwnerID = ""
			if err := s.repo.SaveResourceNode(ctx, node); err != nil {
				return false, err
			}
			s.publish(node)
		}
		if node.RespawnAt == nil || node.RespawnAt.After(now) {
			return false, nil
		}
		return s.respawnOil(ctx, node, now)
	}
	if node.OwnerID == "" {
		return false, nil
	}
	items, err := s.buildings.ListIntersectingFootprint(ctx, node.MapID, node.Tile.X, node.Tile.Y, node.Tile.X, node.Tile.Y)
	if err != nil {
		return false, err
	}
	var well *building.Building
	for i := range items {
		if items[i].Type == building.TypeOilWell && items[i].Tile == node.Tile && items[i].OwnerID == node.OwnerID {
			well = &items[i]
			break
		}
	}
	if well == nil {
		return true, s.ReleaseOilWell(ctx, node.Tile, node.OwnerID)
	}
	if well.State == building.StateRuined || well.Health <= 0 {
		if err := s.CancelOilJobs(ctx, *well); err != nil {
			return false, err
		}
		if err := s.buildings.Delete(ctx, well.ID); err != nil {
			return false, err
		}
		if s.events != nil {
			s.events.Publish(Event{Type: EventBuildingRemoved, ChunkID: world.ChunkID(well.MapID, world.ChunkForTile(well.Tile)), Payload: BuildingRemovedPayload{BuildingID: well.ID, Reason: "destroyed"}})
		}
		return true, s.ReleaseOilWell(ctx, node.Tile, node.OwnerID)
	}
	return false, nil
}

func (s *ResourceService) CheckOilCycle(ctx context.Context, well building.Building) error {
	if well.Type != building.TypeOilWell || well.State != building.StateActive || well.Health <= 0 {
		return apperror.New(apperror.Conflict, "нефтяная вышка не работает")
	}
	node, found, err := s.oilNodeAt(ctx, well.Tile)
	if err != nil {
		return err
	}
	if !found || node.OwnerID != well.OwnerID || node.State != economy.NodeClaimed || node.Amount < catalog.OilExtractionDepletion(well.Level) {
		return apperror.New(apperror.Conflict, "недостаточно нефти в месторождении")
	}
	return nil
}

func (s *ResourceService) CompleteOilCycle(ctx context.Context, well building.Building, now time.Time) error {
	if err := s.CheckOilCycle(ctx, well); err != nil {
		return err
	}
	node, _, err := s.oilNodeAt(ctx, well.Tile)
	if err != nil {
		return err
	}
	node.Amount -= catalog.OilExtractionDepletion(well.Level)
	node.UpdatedAt = now
	if node.Amount == 0 {
		node.State = economy.NodeDepleted
		respawn := now.Add(time.Duration(s.randomIntn(301))*time.Second + 5*time.Minute)
		node.RespawnAt = &respawn
	}
	if err := s.repo.SaveResourceNode(ctx, node); err != nil {
		return err
	}
	s.publish(node)
	return nil
}

func (s *ResourceService) respawnOil(ctx context.Context, node economy.ResourceNode, now time.Time) (bool, error) {
	nodes, err := s.repo.ListResourceNodes(ctx, node.MapID)
	if err != nil {
		return false, err
	}
	occupied := make(map[world.Coord]bool)
	for _, other := range nodes {
		if other.ID != node.ID && other.Resource == economy.ResourceOil && other.State != economy.NodeDepleted {
			occupied[other.Tile] = true
		}
	}
	for attempt := 0; attempt < 256; attempt++ {
		coord := world.Coord{X: s.randomIntn(worldgen.WorldSizeTiles), Y: s.randomIntn(worldgen.WorldSizeTiles)}
		if coord == node.Tile || occupied[coord] {
			continue
		}
		chunk, _, err := s.worlds.GetOrCreateChunk(ctx, node.MapID, world.ChunkForTile(coord))
		if err != nil {
			return false, err
		}
		tile, found := findTile(chunk, coord)
		if !found || tile.SafeZone || tile.Terrain != world.TerrainGrass {
			continue
		}
		buildings, err := s.buildings.ListIntersectingFootprint(ctx, node.MapID, coord.X-2, coord.Y-2, coord.X+2, coord.Y+2)
		if err != nil {
			return false, err
		}
		blocked := false
		for _, item := range buildings {
			if item.State == building.StateRuined {
				continue
			}
			for _, occupied := range item.OccupiedTiles() {
				if abs(occupied.X-coord.X) < 3 && abs(occupied.Y-coord.Y) < 3 {
					blocked = true
					break
				}
			}
			if blocked {
				break
			}
		}
		if blocked {
			continue
		}
		if err := s.changeOilTerrain(ctx, coord, world.TerrainOilWell, "oil_respawned"); err != nil {
			return false, err
		}
		node.Tile = coord
		node.Amount = node.MaxAmount
		node.State = economy.NodeNeutral
		node.RespawnAt = nil
		node.UpdatedAt = now
		if err := s.repo.SaveResourceNode(ctx, node); err != nil {
			return false, err
		}
		s.publish(node)
		return true, nil
	}
	return false, nil
}

func (s *ResourceService) changeOilTerrain(ctx context.Context, coord world.Coord, terrain world.TerrainType, reason string) error {
	chunk, _, err := s.worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(coord))
	if err != nil {
		return err
	}
	tile, found := findTile(chunk, coord)
	if !found {
		return apperror.New(apperror.NotFound, "oil tile not found")
	}
	tile.Terrain = terrain
	if err := s.worlds.UpdateTile(ctx, tile); err != nil {
		return err
	}
	if s.events != nil {
		s.events.Publish(Event{Type: EventTileChanged, ChunkID: world.ChunkID(tile.MapID, tile.Chunk), Payload: TileChangedPayload{Tile: tile, Reason: reason}})
	}
	return nil
}
