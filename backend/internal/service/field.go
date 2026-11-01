package service

import (
	"context"
	"crypto/rand"
	"fmt"
	"math/big"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type FieldService struct {
	economy    *EconomyService
	buildings  BuildingRepository
	now        func() time.Time
	superRoll  func(chanceBps int) bool
	experience *ExperienceService
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

func (s *FieldService) SetExperience(experience *ExperienceService) {
	s.experience = experience
}

func (s *FieldService) StartWindleafCycle(item building.Building, now time.Time, super bool) building.Building {
	return s.startFieldCycle(item, now, super)
}

func (s *FieldService) startFieldCycle(item building.Building, now time.Time, super bool) building.Building {
	if item.State != building.StateActive {
		return item
	}
	crop, ok := economy.FieldCropForBuildingType(string(item.Type), item.Level, super)
	if !ok {
		return item
	}
	stage, _ := economy.FieldStageByIndex(crop, 1)
	readyAt := now.Add(stage.Duration)
	item.FieldStage = 1
	item.FieldStageStartedAt = &now
	item.FieldStageReadyAt = &readyAt
	item.FieldSuperCrop = super
	return item
}

func (s *FieldService) AdvanceWindleaf(ctx context.Context, playerID player.ID, id building.ID) (building.Building, economy.Inventory, error) {
	return s.AdvanceField(ctx, playerID, id)
}

func (s *FieldService) advanceField(ctx context.Context, playerID player.ID, id building.ID) (building.Building, economy.Inventory, error) {
	item, err := s.requireField(ctx, playerID, id)
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	now := s.now()
	if err := s.releaseCompletedFieldPhase(ctx, playerID, &item, now); err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	if item.FieldStage <= 0 {
		if err := s.reservePopulation(ctx, playerID, buildingPopulation(item), fieldReason(item, "workers:start")); err != nil {
			return building.Building{}, economy.Inventory{}, err
		}
		crop, ok := economy.FieldCropForBuildingType(string(item.Type), item.Level, false)
		if !ok {
			_ = s.releasePopulation(ctx, playerID, buildingPopulation(item), fieldReason(item, "workers:start:refund"))
			return building.Building{}, economy.Inventory{}, apperror.New(apperror.Validation, "field crop is not configured")
		}
		item = s.startFieldCycle(item, s.now(), s.superRoll(crop.SuperChanceBps))
		if err := s.buildings.Update(ctx, item); err != nil {
			_ = s.releasePopulation(ctx, playerID, buildingPopulation(item), fieldReason(item, "workers:start:refund"))
			return building.Building{}, economy.Inventory{}, err
		}
		inventory, err := s.currentInventory(ctx, playerID)
		if err != nil {
			return building.Building{}, economy.Inventory{}, err
		}
		return item, inventory, nil
	}
	if item.FieldStageReadyAt == nil || item.FieldStageReadyAt.After(now) {
		return building.Building{}, economy.Inventory{}, apperror.New(apperror.Conflict, "field stage is still growing")
	}
	crop, ok := economy.FieldCropForBuildingType(string(item.Type), item.Level, item.FieldSuperCrop)
	if !ok {
		return building.Building{}, economy.Inventory{}, apperror.New(apperror.Validation, "field crop is not configured")
	}
	if item.FieldStage >= len(crop.Growth) {
		return building.Building{}, economy.Inventory{}, apperror.New(apperror.Conflict, "field is ready to harvest")
	}
	nextStage, ok := economy.FieldStageByIndex(crop, item.FieldStage+1)
	if !ok {
		return building.Building{}, economy.Inventory{}, apperror.New(apperror.Conflict, "field stage is invalid")
	}
	if err := s.reservePopulation(ctx, playerID, buildingPopulation(item), fieldReason(item, "workers:stage_start")); err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	readyAt := now.Add(nextStage.Duration)
	item.FieldStage = nextStage.Index
	item.FieldStageStartedAt = &now
	item.FieldStageReadyAt = &readyAt
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		_ = s.releasePopulation(ctx, playerID, buildingPopulation(item), fieldReason(item, "workers:stage_start:refund"))
		return building.Building{}, economy.Inventory{}, err
	}
	inventory, err := s.currentInventory(ctx, playerID)
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	return item, inventory, nil
}

func (s *FieldService) HarvestWindleaf(ctx context.Context, playerID player.ID, id building.ID) (building.Building, economy.Inventory, error) {
	return s.HarvestField(ctx, playerID, id)
}

func (s *FieldService) harvestField(ctx context.Context, playerID player.ID, id building.ID) (building.Building, economy.Inventory, error) {
	item, err := s.requireField(ctx, playerID, id)
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	now := s.now()
	if err := s.releaseCompletedFieldPhase(ctx, playerID, &item, now); err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	crop, ok := economy.FieldCropForBuildingType(string(item.Type), item.Level, item.FieldSuperCrop)
	if !ok {
		return building.Building{}, economy.Inventory{}, apperror.New(apperror.Validation, "field crop is not configured")
	}
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
	if item.FieldSuperCrop {
		reward = append(reward, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: crop.SuperCoinReward})
		reward = append(reward, crop.SuperReward...)
	} else {
		reward = append(reward, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: crop.CoinReward})
	}
	inventory, _, err := s.economy.Add(ctx, playerID, reward, fieldReason(item, "harvest"))
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	harvestKey := fmt.Sprintf("field:%s:harvest:%d", item.ID, item.FieldStageReadyAt.UnixNano())
	superCrop := item.FieldSuperCrop
	clearWindleafCycle(&item)
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, item); err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	if s.experience != nil {
		reward := catalog.ExperienceForBuilding(item.Type, item.Level).Work
		if superCrop {
			reward *= 3
		}
		if err := s.experience.Award(ctx, playerID, reward, "field:harvest", harvestKey); err != nil {
			return building.Building{}, economy.Inventory{}, err
		}
	}
	inventory, err = s.currentInventory(ctx, playerID)
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	return item, inventory, nil
}

func (s *FieldService) releaseCompletedFieldPhase(ctx context.Context, playerID player.ID, item *building.Building, now time.Time) error {
	if item.FieldStage <= 0 || item.FieldStageStartedAt == nil || item.FieldStageReadyAt == nil || item.FieldStageReadyAt.After(now) {
		return nil
	}
	amount := buildingPopulation(*item)
	reason := fieldReason(*item, "workers:stage_complete")
	item.FieldStageStartedAt = nil
	item.UpdatedAt = now
	if err := s.buildings.Update(ctx, *item); err != nil {
		return err
	}
	return s.releasePopulation(ctx, playerID, amount, reason)
}

func fieldReason(item building.Building, suffix string) string {
	return "field:" + string(item.Type) + ":" + suffix
}

func (s *FieldService) reservePopulation(ctx context.Context, playerID player.ID, amount int, reason string) error {
	if amount <= 0 || s.economy == nil {
		return nil
	}
	_, err := s.economy.Spend(ctx, playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: amount}}, reason)
	if err != nil {
		return apperror.WithFields(apperror.Conflict, "не хватает свободного населения", map[string]string{"population": fmt.Sprintf("need %d", amount)})
	}
	return nil
}

func (s *FieldService) releasePopulation(ctx context.Context, playerID player.ID, amount int, reason string) error {
	if amount <= 0 || s.economy == nil {
		return nil
	}
	_, _, err := s.economy.Add(withoutStarterPopulationBackfill(ctx), playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: amount}}, reason)
	return err
}

func (s *FieldService) currentInventory(ctx context.Context, playerID player.ID) (economy.Inventory, error) {
	if s.economy == nil {
		return economy.Inventory{}, nil
	}
	return s.economy.Inventory(ctx, playerID)
}

func (s *FieldService) requireWindleafBed(ctx context.Context, playerID player.ID, id building.ID) (building.Building, error) {
	return s.requireField(ctx, playerID, id)
}

func (s *FieldService) requireField(ctx context.Context, playerID player.ID, id building.ID) (building.Building, error) {
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
	if !economy.IsFieldCropBuildingType(string(item.Type)) {
		return building.Building{}, apperror.New(apperror.Validation, "building is not a configured field crop")
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
