package service

import (
	"context"

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
	total := inventory.Items["population"]
	return player.NewPopulation(total, player.Population{Builders: 2, Production: 3, Fields: 2}), nil
}
