package service

import (
	"context"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

type FieldService struct {
	economy *EconomyService
}

func NewFieldService(economyService *EconomyService) *FieldService {
	return &FieldService{economy: economyService}
}

func (s *FieldService) HarvestWindleaf(ctx context.Context, playerID player.ID, super bool) (economy.Inventory, error) {
	crop := economy.WindleafCrop()
	reward := make([]economy.ResourceAmount, 0, len(crop.BaseReward)+2)
	if !super {
		reward = append(reward, crop.BaseReward...)
	}
	reward = append(reward, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: crop.CoinReward})
	if super {
		reward = append(reward, crop.SuperReward...)
	}
	inventory, _, err := s.economy.Add(ctx, playerID, reward, "field:windleaf")
	return inventory, err
}
