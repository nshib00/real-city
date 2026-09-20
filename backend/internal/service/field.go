package service

import (
	"context"
	"crypto/rand"
	"math/big"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type FieldService struct {
	economy   *EconomyService
	buildings BuildingRepository
	now       func() time.Time
	superRoll func(chanceBps int) bool
}

func NewFieldService(economyService *EconomyService, buildings BuildingRepository) *FieldService {
	return &FieldService{
		economy:   economyService,
		buildings: buildings,
		now:       func() time.Time { return time.Now().UTC() },
		superRoll: rollSuperWindleaf,
	}
}

func (s *FieldService) SetNowForTest(now func() time.Time) {
	s.now = now
}

func (s *FieldService) SetSuperRollForTest(roll func(chanceBps int) bool) {
	s.superRoll = roll
}

func (s *FieldService) StartWindleafCycle(item building.Building, now time.Time, super bool) building.Building {
	if item.Type != building.TypeFieldBed || item.State != building.StateActive {
		return item
	}
	crop := economy.WindleafCropForLevel(item.Level)
	stage, _ := economy.WindleafStage(crop, 1)
	readyAt := now.Add(stage.Duration)
	item.FieldStage = 1
	item.FieldStageStartedAt = &now
	item.FieldStageReadyAt = &readyAt
	item.FieldSuperCrop = super
	return item
}

func (s *FieldService) AdvanceWindleaf(ctx context.Context, playerID player.ID, id building.ID) (building.Building, error) {
	item, err := s.requireWindleafBed(ctx, playerID, id)
	if err != nil {
		return building.Building{}, err
	}
	if item.FieldStage <= 0 {
		item = s.StartWindleafCycle(item, s.now(), false)
		if err := s.buildings.Update(ctx, item); err != nil {
			return building.Building{}, err
		}
		return item, nil
	}
	now := s.now()
	if item.FieldStageReadyAt == nil || item.FieldStageReadyAt.After(now) {
		return building.Building{}, apperror.New(apperror.Conflict, "field stage is still growing")
	}
	crop := economy.WindleafCropForLevel(item.Level)
	if item.FieldStage >= len(crop.Growth) {
		return building.Building{}, apperror.New(apperror.Conflict, "field is ready to harvest")
	}
	nextStage, ok := economy.WindleafStage(crop, item.FieldStage+1)
	if !ok {
		return building.Building{}, apperror.New(apperror.Conflict, "field stage is invalid")
	}
	readyAt := now.Add(nextStage.Duration)
	item.FieldStage = nextStage.Index
	item.FieldStageStartedAt = &now
	item.FieldStageReadyAt = &readyAt
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		return building.Building{}, err
	}
	return item, nil
}

func (s *FieldService) HarvestWindleaf(ctx context.Context, playerID player.ID, id building.ID) (building.Building, economy.Inventory, error) {
	item, err := s.requireWindleafBed(ctx, playerID, id)
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	now := s.now()
	crop := economy.WindleafCropForLevel(item.Level)
	if item.FieldStage < len(crop.Growth) {
		return building.Building{}, economy.Inventory{}, apperror.New(apperror.Conflict, "field is not ready to harvest")
	}
	if item.FieldStageReadyAt == nil || item.FieldStageReadyAt.After(now) {
		return building.Building{}, economy.Inventory{}, apperror.New(apperror.Conflict, "field is still growing")
	}
	reward := make([]economy.ResourceAmount, 0, len(crop.BaseReward)+2)
	if !item.FieldSuperCrop {
		reward = append(reward, crop.BaseReward...)
	}
	reward = append(reward, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: crop.CoinReward})
	if item.FieldSuperCrop {
		reward = append(reward, crop.SuperReward...)
	}
	inventory, _, err := s.economy.Add(ctx, playerID, reward, "field:windleaf")
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	item = s.StartWindleafCycle(item, now, s.superRoll(crop.SuperChanceBps))
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	return item, inventory, nil
}

func (s *FieldService) requireWindleafBed(ctx context.Context, playerID player.ID, id building.ID) (building.Building, error) {
	if s.buildings == nil {
		return building.Building{}, apperror.New(apperror.Internal, "building repository is not configured")
	}
	item, err := s.buildings.FindByID(ctx, id)
	if err != nil {
		return building.Building{}, err
	}
	if item.OwnerID != string(playerID) {
		return building.Building{}, apperror.New(apperror.Forbidden, "building belongs to another player")
	}
	if item.Type != building.TypeFieldBed {
		return building.Building{}, apperror.New(apperror.Validation, "building is not a windleaf bed")
	}
	if item.State != building.StateActive {
		return building.Building{}, apperror.New(apperror.Conflict, "field is not active")
	}
	return item, nil
}

func rollSuperWindleaf(chanceBps int) bool {
	if chanceBps <= 0 {
		return false
	}
	if chanceBps >= 10_000 {
		return true
	}
	value, err := rand.Int(rand.Reader, big.NewInt(10_000))
	if err != nil {
		return false
	}
	return int(value.Int64()) < chanceBps
}
