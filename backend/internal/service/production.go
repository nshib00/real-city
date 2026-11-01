package service

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type ProductionService struct {
	repo       EconomyRepository
	economy    *EconomyService
	log        *slog.Logger
	now        func() time.Time
	events     *EventBus
	actions    ActionRepository
	buildings  BuildingRepository
	experience *ExperienceService
	resources  *ResourceService
	randFloat  func() float64
	uow        UnitOfWork
}

func NewProductionService(repo EconomyRepository, economyService *EconomyService, log *slog.Logger) *ProductionService {
	return &ProductionService{repo: repo, economy: economyService, log: log, now: func() time.Time { return time.Now().UTC() }, randFloat: rand.Float64}
}

func (s *ProductionService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *ProductionService) SetActionQueue(actions ActionRepository) {
	s.actions = actions
}

func (s *ProductionService) SetBuildings(buildings BuildingRepository) {
	s.buildings = buildings
}

func (s *ProductionService) SetResources(resources *ResourceService) {
	s.resources = resources
}

func (s *ProductionService) SetExperience(experience *ExperienceService) {
	s.experience = experience
}

func (s *ProductionService) Recipes(ctx context.Context) ([]economy.ProductionRecipe, error) {
	_ = ctx
	recipes := make([]economy.ProductionRecipe, 0, len(catalog.ProductionRecipes)+23)
	for _, recipe := range catalog.ProductionRecipes {
		if minimum, ok := catalog.IndustryExtraRecipeMinimum(recipe.ID); ok {
			for level := minimum; level <= 10; level++ {
				levelRecipe, _ := catalog.RecipeForBuildingLevel(recipe.ID, level)
				recipes = append(recipes, levelRecipe)
			}
			continue
		}
		if catalog.IsIndustryLevelRecipe(recipe.ID) {
			for level := 1; level <= catalog.IndustryRecipeLevels(recipe.ID); level++ {
				levelRecipe, _ := catalog.RecipeForBuildingLevel(recipe.ID, level)
				recipes = append(recipes, levelRecipe)
			}
			continue
		}
		if recipe.ID != "planks_from_wood" && recipe.ID != "clay_quarry_run" {
			recipes = append(recipes, recipe)
			continue
		}
		maxLevel := 13
		if recipe.ID == "clay_quarry_run" {
			maxLevel = 12
		}
		for level := 1; level <= maxLevel; level++ {
			levelRecipe, _ := catalog.RecipeForBuildingLevel(recipe.ID, level)
			recipes = append(recipes, levelRecipe)
		}
	}
	for level := 1; level <= 3; level++ {
		recipes = append(recipes, catalog.OilExtractionRecipe(level))
	}
	return recipes, nil
}

func (s *ProductionService) List(ctx context.Context, playerID player.ID) ([]economy.ProductionJob, error) {
	return s.repo.ListProductionJobs(ctx, playerID)
}

func (s *ProductionService) start(ctx context.Context, playerID player.ID, buildingID string, recipeID string) (economy.ProductionJob, economy.Inventory, error) {
	recipe, ok := catalog.RecipeByID(recipeID)
	if !ok {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.NotFound, "production recipe not found")
	}
	if s.buildings != nil {
		item, err := s.buildings.FindByID(ctx, building.ID(buildingID))
		if err != nil {
			return economy.ProductionJob{}, economy.Inventory{}, err
		}
		if item.OwnerID != string(playerID) {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Forbidden, "building belongs to another player")
		}
		if item.State != building.StateActive || item.Health <= 0 {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "building is not active")
		}
		if string(item.Type) != recipe.BuildingType {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Validation, "recipe does not match building type")
		}
		recipe, _ = catalog.RecipeForBuildingLevel(recipeID, item.Level)
		if item.Level < recipe.RequiredLevel {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "building level is too low for recipe")
		}
		if recipeID == catalog.OilExtractionRecipeID {
			if s.resources == nil {
				return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "нефтяная скважина недоступна")
			}
			if err := s.resources.CheckOilCycle(ctx, item); err != nil {
				return economy.ProductionJob{}, economy.Inventory{}, err
			}
		}
	}
	jobs, err := s.repo.ListProductionJobs(ctx, playerID)
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	for _, job := range jobs {
		if job.BuildingID == buildingID && (job.State == economy.ProductionRunning || job.State == economy.ProductionReady) {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "building already has active production")
		}
	}
	if err := s.reservePopulation(ctx, playerID, recipe.Workers, "production:workers:"+recipe.ID); err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	inventory, err := s.economy.Spend(ctx, playerID, economy.WithFuelCost(recipe.Input, recipe), "production:"+recipe.ID)
	if err != nil {
		_ = s.releasePopulation(ctx, playerID, recipe.Workers, "production:workers:refund:"+recipe.ID)
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	now := s.now()
	job := economy.ProductionJob{
		ID:          economy.ProductionJobID(newID("job")),
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
		_ = s.releasePopulation(ctx, playerID, recipe.Workers, "production:workers:refund:"+recipe.ID)
		_, _, _ = s.economy.Add(ctx, playerID, economy.WithFuelCost(recipe.Input, recipe), "production:refund:"+recipe.ID)
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	if err := s.scheduleCompletion(ctx, job); err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
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

func (s *ProductionService) completeAt(ctx context.Context, playerID player.ID, id economy.ProductionJobID, now time.Time) (economy.ProductionJob, economy.Inventory, error) {
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
	if job.State != economy.ProductionRunning && job.State != economy.ProductionReady {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "production job is not running")
	}
	if job.State == economy.ProductionRunning && job.CompletesAt.After(now) {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "production job is not complete yet")
	}
	recipe, ok := catalog.RecipeByID(job.RecipeID)
	if !ok {
		return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.NotFound, "production recipe not found")
	}
	var completionBuilding *building.Building
	if s.buildings != nil {
		item, err := s.buildings.FindByID(ctx, building.ID(job.BuildingID))
		if err != nil || item.OwnerID != string(playerID) || item.Health <= 0 || item.State == building.StateRuined || string(item.Type) != recipe.BuildingType {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "Постройка больше не может выдать продукцию")
		}
		if err == nil && string(item.Type) == recipe.BuildingType {
			recipe, _ = catalog.RecipeForBuildingLevel(job.RecipeID, item.Level)
			completionBuilding = &item
		}
	}
	if job.RecipeID == catalog.OilExtractionRecipeID {
		if s.resources == nil || s.buildings == nil {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "нефтяная скважина недоступна")
		}
		well, err := s.buildings.FindByID(ctx, building.ID(job.BuildingID))
		if err != nil || well.OwnerID != string(playerID) || well.State != building.StateActive {
			return economy.ProductionJob{}, economy.Inventory{}, apperror.New(apperror.Conflict, "нефтяная вышка не работает")
		}
		if err := s.resources.CompleteOilCycle(ctx, well, now); err != nil {
			return economy.ProductionJob{}, economy.Inventory{}, err
		}
	}
	previousState := job.State
	job.State = economy.ProductionCompleted
	job.UpdatedAt = now
	if err := s.repo.SaveProductionJob(ctx, job); err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	if previousState == economy.ProductionRunning {
		if err := s.releasePopulation(ctx, playerID, recipe.Workers, "production:workers:complete:"+recipe.ID); err != nil {
			return economy.ProductionJob{}, economy.Inventory{}, err
		}
	}
	output := append([]economy.ResourceAmount(nil), recipe.Output...)
	rareOutput := s.rollRareOutput(recipe)
	output = append(output, rareOutput...)
	inventory, _, err := s.economy.Add(ctx, playerID, output, "production:"+recipe.ID)
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	if s.experience != nil && s.buildings != nil {
		if completionBuilding == nil {
			item, err := s.buildings.FindByID(ctx, building.ID(job.BuildingID))
			if err != nil {
				return economy.ProductionJob{}, economy.Inventory{}, err
			}
			completionBuilding = &item
		}
		reward := catalog.ExperienceForBuilding(completionBuilding.Type, completionBuilding.Level).Work
		if err := s.experience.Award(ctx, playerID, reward, "production:complete", "production:"+string(job.ID)+":complete"); err != nil {
			return economy.ProductionJob{}, economy.Inventory{}, err
		}
	}
	s.publish(ctx, job, inventory)
	s.log.Info("economy.production.completed", "event", "economy.production.completed", "player_id", playerID, "job_id", job.ID, "recipe_id", recipe.ID, "output", output, "rare_output", rareOutput, "rare_chances", recipe.RareOutput)
	return job, inventory, nil
}

func (s *ProductionService) rollRareOutput(recipe economy.ProductionRecipe) []economy.ResourceAmount {
	if len(recipe.RareOutput) == 0 {
		return nil
	}
	roll := s.randFloat
	if roll == nil {
		roll = rand.Float64
	}
	output := make([]economy.ResourceAmount, 0, len(recipe.RareOutput))
	draws := map[economy.ResourceType]float64{}
	thresholds := map[economy.ResourceType]float64{}
	awarded := map[economy.ResourceType]bool{}
	for _, item := range recipe.RareOutput {
		if item.Amount <= 0 || item.Chance <= 0 {
			continue
		}
		if _, ok := draws[item.Resource]; !ok {
			draws[item.Resource] = roll()
		}
		thresholds[item.Resource] += item.Chance
		if !awarded[item.Resource] && draws[item.Resource] < thresholds[item.Resource] {
			output = append(output, economy.ResourceAmount{Resource: item.Resource, Amount: item.Amount})
			awarded[item.Resource] = true
		}
	}
	return output
}

func (s *ProductionService) readyAt(ctx context.Context, playerID player.ID, id economy.ProductionJobID, now time.Time) (economy.ProductionJob, error) {
	job, err := s.repo.FindProductionJob(ctx, id)
	if err != nil {
		return economy.ProductionJob{}, err
	}
	if job.PlayerID != string(playerID) {
		return economy.ProductionJob{}, apperror.New(apperror.Forbidden, "production job belongs to another player")
	}
	if job.State == economy.ProductionReady || job.State == economy.ProductionCompleted || job.State == economy.ProductionCancelled {
		return job, nil
	}
	if job.State != economy.ProductionRunning {
		return economy.ProductionJob{}, apperror.New(apperror.Conflict, "production job is not running")
	}
	if job.CompletesAt.After(now) {
		return economy.ProductionJob{}, apperror.New(apperror.Conflict, "production job is not complete yet")
	}
	recipe, ok := catalog.RecipeByID(job.RecipeID)
	if !ok {
		return economy.ProductionJob{}, apperror.New(apperror.NotFound, "production recipe not found")
	}
	if s.buildings != nil {
		item, err := s.buildings.FindByID(ctx, building.ID(job.BuildingID))
		if err == nil && string(item.Type) == recipe.BuildingType {
			recipe, _ = catalog.RecipeForBuildingLevel(job.RecipeID, item.Level)
		}
	}
	job.State = economy.ProductionReady
	job.UpdatedAt = now
	if err := s.repo.SaveProductionJob(ctx, job); err != nil {
		return economy.ProductionJob{}, err
	}
	if err := s.releasePopulation(ctx, playerID, recipe.Workers, "production:workers:ready:"+recipe.ID); err != nil {
		return economy.ProductionJob{}, err
	}
	s.log.Info("economy.production.ready", "event", "economy.production.ready", "player_id", playerID, "job_id", job.ID, "recipe_id", job.RecipeID)
	return job, nil
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
		if _, err := s.ReadyAt(ctx, player.ID(job.PlayerID), job.ID, now); err != nil {
			return completed, err
		}
		completed++
	}
	return completed, nil
}

func (s *ProductionService) cancel(ctx context.Context, playerID player.ID, id economy.ProductionJobID) (economy.ProductionJob, error) {
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
	if recipe, ok := s.recipeForJob(ctx, job); ok {
		if err := s.releasePopulation(ctx, playerID, recipe.Workers, "production:workers:cancel:"+recipe.ID); err != nil {
			return economy.ProductionJob{}, err
		}
	}
	s.log.Info("economy.production.cancelled", "event", "economy.production.cancelled", "player_id", playerID, "job_id", job.ID)
	return job, nil
}

func (s *ProductionService) reservePopulation(ctx context.Context, playerID player.ID, amount int, reason string) error {
	if amount <= 0 || s.economy == nil {
		return nil
	}
	_, err := s.economy.Spend(ctx, playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: amount}}, reason)
	if err != nil {
		return apperror.WithFields(apperror.Conflict, "не хватает свободного населения", map[string]string{"population": fmt.Sprintf("need %d", amount)})
	}
	return nil
}

func (s *ProductionService) releasePopulation(ctx context.Context, playerID player.ID, amount int, reason string) error {
	if amount <= 0 || s.economy == nil {
		return nil
	}
	_, _, err := s.economy.Add(withoutStarterPopulationBackfill(ctx), playerID, []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: amount}}, reason)
	return err
}

func (s *ProductionService) recipeForJob(ctx context.Context, job economy.ProductionJob) (economy.ProductionRecipe, bool) {
	recipe, ok := catalog.RecipeByID(job.RecipeID)
	if !ok {
		return economy.ProductionRecipe{}, false
	}
	if s.buildings != nil {
		item, err := s.buildings.FindByID(ctx, building.ID(job.BuildingID))
		if err == nil && string(item.Type) == recipe.BuildingType {
			recipe, _ = catalog.RecipeForBuildingLevel(job.RecipeID, item.Level)
		}
	}
	return recipe, true
}

func (s *ProductionService) publish(ctx context.Context, job economy.ProductionJob, inventory economy.Inventory) {
	if s.events == nil {
		return
	}
	publishEvent(ctx, s.events, Event{
		Type:     EventProductionDone,
		PlayerID: player.ID(job.PlayerID),
		Payload:  ProductionPayload{Job: job, Inventory: inventory},
	})
}
