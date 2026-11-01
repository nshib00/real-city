package service

import (
	"context"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

type PopulationService struct {
	economy *EconomyService
}

func NewPopulationService(economyService *EconomyService) *PopulationService {
	return &PopulationService{economy: economyService}
}

func (s *PopulationService) Summary(ctx context.Context, playerID player.ID) (player.Population, error) {
	inventory, err := s.economy.Inventory(ctx, playerID)
	if err != nil {
		return player.Population{}, err
	}
	busy := player.Population{}
	buildingLevels := make(map[string]int)
	if s.economy.buildings != nil {
		buildings, err := s.economy.buildings.ListByPlayer(ctx, playerID)
		if err != nil {
			return player.Population{}, err
		}
		for _, item := range buildings {
			buildingLevels[string(item.ID)] = item.Level
			if item.State == building.StateBuilding && item.CompletesAt != nil {
				busy.Builders += buildingPopulation(item)
			}
			if item.FieldStageStartedAt != nil {
				busy.Fields += buildingPopulation(item)
			}
		}
	}
	jobs, err := s.economy.repo.ListProductionJobs(ctx, playerID)
	if err != nil {
		return player.Population{}, err
	}
	for _, job := range jobs {
		if job.State != economy.ProductionRunning {
			continue
		}
		if recipe, ok := catalog.RecipeForBuildingLevel(job.RecipeID, buildingLevels[job.BuildingID]); ok {
			busy.Production += recipe.Workers
		}
	}
	if repo, ok := s.economy.buildings.(RepairRepository); ok {
		busy.Repair, err = repo.RepairWorkers(ctx, playerID)
		if err != nil {
			return player.Population{}, err
		}
	}
	free := inventory.Items[economy.ResourcePopulation]
	total := free + busy.Builders + busy.Production + busy.Fields + busy.Repair
	return player.NewPopulation(total, busy), nil
}
