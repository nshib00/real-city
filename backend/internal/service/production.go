package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ProductionService struct {
	repo    EconomyRepository
	economy *EconomyService
	log     *slog.Logger
	now     func() time.Time
}

func NewProductionService(repo EconomyRepository, economyService *EconomyService, log *slog.Logger) *ProductionService {
	return &ProductionService{repo: repo, economy: economyService, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *ProductionService) Recipes(ctx context.Context) ([]economy.ProductionRecipe, error) {
	_ = ctx
	return catalog.ProductionRecipes, nil
}

func (s *ProductionService) List(ctx context.Context, playerID player.ID) ([]economy.ProductionJob, error) {
	return s.repo.ListProductionJobs(ctx, playerID)
}

func (s *ProductionService) Start(ctx context.Context, playerID player.ID, buildingID string, recipeID string) (economy.ProductionJob, economy.Inventory, error) {
	recipe, ok := catalog.RecipeByID(recipeID)
	if !ok {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.NotFound, "production recipe not found")
	}
	inventory, err := s.economy.Spend(ctx, playerID, recipe.Input, "production:"+recipe.ID)
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	now := s.now()
	job := economy.ProductionJob{
		ID:          economy.ProductionJobID(fmt.Sprintf("job_%d_%s", now.UnixNano(), recipe.ID)),
		PlayerID:    string(playerID),
		BuildingID:  buildingID,
		RecipeID:    recipe.ID,
		State:       economy.ProductionRunning,
		StartedAt:   now,
		CompletesAt: now.Add(recipe.Duration),
		CreatedAt:   now,
		UpdatedAt:   now,
	}
	if err := s.repo.SaveProductionJob(ctx, job); err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	s.log.Info("economy.production.started", "event", "economy.production.started", "player_id", playerID, "job_id", job.ID, "recipe_id", recipe.ID)
	return job, inventory, nil
}

func (s *ProductionService) Complete(ctx context.Context, playerID player.ID, id economy.ProductionJobID) (economy.ProductionJob, economy.Inventory, error) {
	job, err := s.repo.FindProductionJob(ctx, id)
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	if job.PlayerID != string(playerID) {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Forbidden, "production job belongs to another player")
	}
	if job.State == economy.ProductionCompleted {
		inventory, err := s.economy.Inventory(ctx, playerID)
		return job, inventory, err
	}
	if job.State != economy.ProductionRunning {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "production job is not running")
	}
	if job.CompletesAt.After(s.now()) {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "production job is not complete yet")
	}
	recipe, ok := catalog.RecipeByID(job.RecipeID)
	if !ok {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.NotFound, "production recipe not found")
	}
	job.State = economy.ProductionCompleted
	job.UpdatedAt = s.now()
	if err := s.repo.SaveProductionJob(ctx, job); err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	inventory, _, err := s.economy.Add(ctx, playerID, recipe.Output, "production:"+recipe.ID)
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	s.log.Info("economy.production.completed", "event", "economy.production.completed", "player_id", playerID, "job_id", job.ID, "recipe_id", recipe.ID)
	return job, inventory, nil
}

func (s *ProductionService) Cancel(ctx context.Context, playerID player.ID, id economy.ProductionJobID) (economy.ProductionJob, error) {
	job, err := s.repo.FindProductionJob(ctx, id)
	if err != nil {
		return economy.ProductionJob{}, err
	}
	if job.PlayerID != string(playerID) {
		return economy.ProductionJob{}, apperror.New(apperror.Forbidden, "production job belongs to another player")
	}
	if job.State != economy.ProductionRunning {
		return economy.ProductionJob{}, apperror.New(apperror.Conflict, "only running production jobs can be cancelled")
	}
	job.State = economy.ProductionCancelled
	job.UpdatedAt = s.now()
	if err := s.repo.SaveProductionJob(ctx, job); err != nil {
		return economy.ProductionJob{}, err
	}
	s.log.Info("economy.production.cancelled", "event", "economy.production.cancelled", "player_id", playerID, "job_id", job.ID)
	return job, nil
}
