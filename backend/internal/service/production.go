package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/action"
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
	events  *EventBus
	actions ActionRepository
}

func NewProductionService(repo EconomyRepository, economyService *EconomyService, log *slog.Logger) *ProductionService {
	return &ProductionService{repo: repo, economy: economyService, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *ProductionService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *ProductionService) SetActionQueue(actions ActionRepository) {
	s.actions = actions
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
	inventory, err := s.economy.Spend(ctx, playerID, economy.WithFuelCost(recipe.Input, recipe), "production:"+recipe.ID)
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
	_ = s.scheduleCompletion(ctx, job)
	s.log.Info("economy.production.started", "event", "economy.production.started", "player_id", playerID, "job_id", job.ID, "recipe_id", recipe.ID)
	return job, inventory, nil
}

func (s *ProductionService) scheduleCompletion(ctx context.Context, job economy.ProductionJob) error {
	if s.actions == nil {
		return nil
	}
	now := s.now()
	return s.actions.Append(ctx, action.NewGameAction(
		action.ID(fmt.Sprintf("act_production_%s_%d", job.ID, job.CompletesAt.UnixNano())),
		action.TypeCompleteProduction,
		fmt.Sprintf("production:%s:complete:%d", job.ID, job.CompletesAt.UnixNano()),
		action.ObjectRef{ID: job.PlayerID, Type: "player"},
		action.ObjectRef{ID: string(job.ID), Type: "production_job"},
		job.CompletesAt,
		now,
	))
}

func (s *ProductionService) Complete(ctx context.Context, playerID player.ID, id economy.ProductionJobID) (economy.ProductionJob, economy.Inventory, error) {
	return s.CompleteAt(ctx, playerID, id, s.now())
}

func (s *ProductionService) CompleteAt(ctx context.Context, playerID player.ID, id economy.ProductionJobID, now time.Time) (economy.ProductionJob, economy.Inventory, error) {
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
	if job.CompletesAt.After(now) {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "production job is not complete yet")
	}
	recipe, ok := catalog.RecipeByID(job.RecipeID)
	if !ok {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.NotFound, "production recipe not found")
	}
	job.State = economy.ProductionCompleted
	job.UpdatedAt = now
	if err := s.repo.SaveProductionJob(ctx, job); err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	inventory, _, err := s.economy.Add(ctx, playerID, recipe.Output, "production:"+recipe.ID)
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	s.publish(job, inventory)
	s.log.Info("economy.production.completed", "event", "economy.production.completed", "player_id", playerID, "job_id", job.ID, "recipe_id", recipe.ID)
	return job, inventory, nil
}

func (s *ProductionService) CompleteDue(ctx context.Context, now time.Time, limit int) (int, error) {
	jobs, err := s.repo.ListDueProductionJobs(ctx, now, limit)
	if err != nil {
		return 0, err
	}
	completed := 0
	previousNow := s.now
	s.now = func() time.Time { return now }
	defer func() { s.now = previousNow }()
	ctx = WithoutCatchUp(ctx)
	for _, job := range jobs {
		if job.State != economy.ProductionRunning || job.CompletesAt.After(now) {
			continue
		}
		if _, _, err := s.CompleteAt(ctx, player.ID(job.PlayerID), job.ID, now); err != nil {
			return completed, err
		}
		completed++
	}
	return completed, nil
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

func (s *ProductionService) publish(job economy.ProductionJob, inventory economy.Inventory) {
	if s.events == nil {
		return
	}
	s.events.Publish(Event{
		Type:     EventProductionDone,
		PlayerID: player.ID(job.PlayerID),
		Payload:  ProductionPayload{Job: job, Inventory: inventory},
	})
}
