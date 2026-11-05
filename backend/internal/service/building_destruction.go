package service

import (
	"context"
	"fmt"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

// HandleDestruction is called inside the transaction that applies the lethal hit.
// Both player weapons and monster AI use this path, including wild monsters.
func (s *BuildingService) HandleDestruction(ctx context.Context, before, after building.Building, attacker player.ID, now time.Time) error {
	if before.ID != after.ID || before.Health <= 0 || before.State == building.StateRuined || after.Health != 0 || after.State != building.StateRuined {
		return nil
	}
	workers := 0
	if before.State == building.StateBuilding && before.CompletesAt != nil {
		workers += buildingPopulation(before)
	}
	if before.FieldStageStartedAt != nil {
		workers += buildingPopulation(before)
	}
	if catalog.IsDefenseWeapon(before.Type) && before.CannonEnabled {
		workers++
	}
	if before.Type == building.TypeTower && before.TowerWatchkeeperAssigned {
		workers++
	}
	if s.economy != nil {
		if repairs, ok := s.buildings.(RepairRepository); ok {
			job, err := repairs.PendingRepair(ctx, before.ID)
			if err == nil {
				workers += job.Workers
				if err := repairs.FinishRepair(ctx, job.ID, "cancelled"); err != nil {
					return err
				}
			} else if !isNotFound(err) {
				return err
			}
		}
		jobs, err := s.economy.repo.ListProductionJobs(ctx, player.ID(before.OwnerID))
		if err != nil {
			return err
		}
		for _, job := range jobs {
			if job.BuildingID != string(before.ID) || (job.State != economy.ProductionRunning && job.State != economy.ProductionReady) {
				continue
			}
			if job.State == economy.ProductionRunning {
				recipe, ok := catalog.RecipeForBuildingLevel(job.RecipeID, before.Level)
				if !ok {
					return apperror.New(apperror.Conflict, "destroyed building production recipe not found")
				}
				workers += recipe.Workers
			}
			job.State = economy.ProductionCancelled
			job.UpdatedAt = now
			if err := s.economy.repo.SaveProductionJob(ctx, job); err != nil {
				return err
			}
		}
		if workers > 0 && before.OwnerID != "" {
			if _, _, err := s.economy.Add(withoutStarterPopulationBackfill(WithoutCatchUp(ctx)), player.ID(before.OwnerID), []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: workers}}, "building:destroyed:workers:"+string(before.ID)); err != nil {
				return err
			}
		}
	}
	after.CompletesAt = nil
	clearWindleafCycle(&after)
	after.CannonEnabled = false
	after.TowerWatchkeeperAssigned = false
	after.CannonNextAttackAt = nil
	after.CannonTargetID = ""
	if before.Type == building.TypeOilWell || catalog.IsRuin(before.Type) {
		if before.Type == building.TypeOilWell && s.resources != nil {
			if err := s.resources.ReleaseOilWell(ctx, before.Tile, before.OwnerID); err != nil {
				return err
			}
		}
		if err := s.buildings.Delete(ctx, before.ID); err != nil {
			return err
		}
	} else if err := s.buildings.Update(ctx, after); err != nil {
		return err
	}
	if s.experience == nil || attacker == "" || before.OwnerID == "" || before.OwnerID == string(attacker) {
		return nil
	}
	reward := catalog.ExperienceForBuilding(before.Type, before.Level).Destruction
	if reward <= 0 {
		return apperror.New(apperror.Conflict, "building destruction XP is not configured")
	}
	return s.experience.Award(ctx, attacker, reward, "building:destroy", fmt.Sprintf("building:%s:destroy", before.ID))
}

// DestructionTransaction also supplies rollback for the in-memory game mode.
func (s *BuildingService) DestructionTransaction(ctx context.Context, uow UnitOfWork, work func(context.Context) error, repositories ...any) error {
	if uow == nil {
		repositories = append(repositories, s.buildings)
		repositories = append(repositories, s.pvpProtection)
		if s.actions != nil {
			repositories = append(repositories, s.actions)
		}
		if s.economy != nil {
			repositories = append(repositories, s.economy.repo)
		}
		if s.experience != nil {
			repositories = append(repositories, s.experience.players)
		}
		uow = snapshotUnitOfWork{repositories}
	}
	return transactional(ctx, uow, work)
}
