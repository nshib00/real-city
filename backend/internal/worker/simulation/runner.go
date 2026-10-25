package simulation

import (
	"context"
	"errors"
	"log/slog"
	"runtime/debug"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

type Runner struct {
	actions    service.ActionRepository
	uow        service.UnitOfWork
	buildings  *service.BuildingService
	production *service.ProductionService
	resources  *service.ResourceService
	forests    *service.ForestService
	spawner    *MonsterSpawner
	monsters   *MonsterAI
	cannons    *service.CannonService
	combat     *service.CombatService
	raids      *service.RaidService
	log        *slog.Logger
	cfg        config.SimulationConfig
	now        func() time.Time
}

type TickResult struct {
	ActionsProcessed    int
	BuildingsCompleted  int
	ProductionCompleted int
	ResourcesRespawned  int
	MonstersSpawned     int
	MonstersProcessed   int
	CannonsFired        int
	Failures            int
}

func NewRunner(actions service.ActionRepository, uow service.UnitOfWork, buildings *service.BuildingService, production *service.ProductionService, resources *service.ResourceService, log *slog.Logger, cfg config.SimulationConfig) *Runner {
	if cfg.TickInterval <= 0 {
		cfg.TickInterval = time.Second
	}
	if cfg.BatchSize <= 0 {
		cfg.BatchSize = 100
	}
	if cfg.LockTTL <= 0 {
		cfg.LockTTL = 15 * time.Second
	}
	return &Runner{actions: actions, uow: uow, buildings: buildings, production: production, resources: resources, log: log, cfg: cfg, now: func() time.Time { return time.Now().UTC() }}
}

func (r *Runner) SetMonsterAI(monsters *MonsterAI) {
	r.monsters = monsters
}

func (r *Runner) SetCannonService(cannons *service.CannonService) {
	r.cannons = cannons
}

func (r *Runner) SetCombatService(combat *service.CombatService) { r.combat = combat }
func (r *Runner) SetRaidService(raids *service.RaidService) { r.raids = raids }

func (r *Runner) SetMonsterSpawner(spawner *MonsterSpawner) {
	r.spawner = spawner
}

func (r *Runner) SetForestService(forests *service.ForestService) {
	r.forests = forests
}

func (r *Runner) Run(ctx context.Context) error {
	ticker := time.NewTicker(r.cfg.TickInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			_, _ = r.tick(ctx, "scheduled")
		}
	}
}

func (r *Runner) Tick(ctx context.Context) (result TickResult, err error) {
	return r.tick(ctx, "catch_up")
}

func (r *Runner) tick(ctx context.Context, mode string) (result TickResult, err error) {
	start := r.now()
	started := time.Now()
	panicked := false
	r.log.Info("simulation.tick.start", "event", "simulation.tick.start")
	defer func() {
		if recovered := recover(); recovered != nil {
			panicked = true
			result.Failures++
			err = errors.New("simulation tick panic")
			r.log.Error("simulation.tick.panic", "event", "simulation.tick.panic", "panic", recovered, "stack", string(debug.Stack()))
		}
		status := "ok"
		if err != nil || result.Failures != 0 {
			status = "error"
		}
		if panicked {
			status = "panic"
		}
		observability.Tick(mode, started, status, status == "ok")
		duration := r.now().Sub(start)
		level := slog.LevelInfo
		if duration > r.cfg.TickInterval {
			level = slog.LevelWarn
		}
		r.log.Log(ctx, level, "simulation.tick.finish", "event", "simulation.tick.finish", "duration_ms", duration.Milliseconds(), "actions", result.ActionsProcessed, "buildings", result.BuildingsCompleted, "production", result.ProductionCompleted, "resources", result.ResourcesRespawned, "monster_spawns", result.MonstersSpawned, "monsters", result.MonstersProcessed, "cannons_fired", result.CannonsFired, "failures", result.Failures)
	}()

	now := r.now()
	if r.actions != nil {
		stageStart := time.Now()
		processed, failures, err := r.processActions(ctx, now)
		if mode == "scheduled" {
			observability.Stage("actions", stageStart, processed, failures, r.cfg.BatchSize, err)
		}
		result.ActionsProcessed = processed
		result.Failures += failures
		if err != nil {
			return result, err
		}
	}
	if r.buildings != nil {
		stageStart := time.Now()
		result.BuildingsCompleted, err = r.buildings.CompleteDue(ctx, now, r.cfg.BatchSize)
		if mode == "scheduled" {
			observability.Stage("buildings", stageStart, result.BuildingsCompleted, boolCount(err != nil), r.cfg.BatchSize, err)
		}
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.production != nil {
		stageStart := time.Now()
		result.ProductionCompleted, err = r.production.CompleteDue(ctx, now, r.cfg.BatchSize)
		if mode == "scheduled" {
			observability.Stage("production", stageStart, result.ProductionCompleted, boolCount(err != nil), r.cfg.BatchSize, err)
		}
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.resources != nil {
		stageStart := time.Now()
		result.ResourcesRespawned, err = r.resources.Tick(ctx, now, r.cfg.BatchSize)
		if mode == "scheduled" {
			observability.Stage("resources", stageStart, result.ResourcesRespawned, boolCount(err != nil), r.cfg.BatchSize, err)
		}
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.spawner != nil {
		stageStart := time.Now()
		result.MonstersSpawned, err = r.spawner.Tick(ctx, now, r.cfg.BatchSize)
		if mode == "scheduled" {
			observability.Stage("monster_spawning", stageStart, result.MonstersSpawned, boolCount(err != nil), r.cfg.BatchSize, err)
		}
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.monsters != nil {
		stageStart := time.Now()
		result.MonstersProcessed, err = r.monsters.Tick(ctx, now, r.cfg.BatchSize)
		if mode == "scheduled" {
			observability.Stage("monster_ai", stageStart, result.MonstersProcessed, boolCount(err != nil), r.cfg.BatchSize, err)
		}
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.cannons != nil {
		result.CannonsFired, err = r.cannons.Tick(ctx, now, r.cfg.BatchSize)
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	return result, nil
}

func boolCount(v bool) int {
	if v {
		return 1
	}
	return 0
}

func (r *Runner) CatchUp(ctx context.Context, playerID string) error {
	if r.cfg.CatchUpLimit <= 0 {
		return nil
	}
	_, err := r.tick(WithoutActionQueue(ctx), "catch_up")
	if err != nil {
		r.log.Warn("simulation.catch_up.failed", "event", "simulation.catch_up.failed", "player_id", playerID, "error", err.Error())
	}
	return err
}

func (r *Runner) processActions(ctx context.Context, now time.Time) (int, int, error) {
	if ctx.Value(skipActionQueueKey{}) == true {
		return 0, 0, nil
	}
	actions, err := r.actions.FetchDue(ctx, now, r.cfg.BatchSize, r.cfg.LockTTL)
	if err != nil {
		return 0, 1, err
	}
	for range actions {
		observability.Action("fetched")
	}
	failures := 0
	for _, item := range actions {
		err := r.handleAction(ctx, item, now)
		if err != nil {
			failures++
			retryAt := now.Add(backoff(item.Attempts))
			if markErr := r.actions.MarkFailed(ctx, item.ID, err.Error(), retryAt, now); markErr != nil {
				observability.Action("failed")
				return len(actions), failures, markErr
			}
			observability.Action("retried")
			r.log.Warn("simulation.action.failed", "event", "simulation.action.failed", "action_id", item.ID, "action_type", item.Type, "attempts", item.Attempts+1, "retry_at", retryAt, "error", err.Error())
			continue
		}
		if err := r.actions.MarkDone(ctx, item.ID, now); err != nil {
			observability.Action("failed")
			return len(actions), failures + 1, err
		}
		observability.Action("processed")
		r.log.Info("simulation.action.done", "event", "simulation.action.done", "action_id", item.ID, "action_type", item.Type)
	}
	return len(actions), failures, nil
}

func (r *Runner) handleAction(ctx context.Context, item action.GameAction, now time.Time) error {
	run := func(ctx context.Context) error {
		switch item.Type {
		case action.TypeCompleteBuilding:
			if r.buildings == nil {
				return nil
			}
			_, err := r.buildings.CompleteAt(ctx, building.ID(item.Target.ID), player.ID(item.Actor.ID), now)
			return err
		case action.TypeCompleteProduction:
			if r.production == nil {
				return nil
			}
			_, err := r.production.ReadyAt(ctx, player.ID(item.Actor.ID), economy.ProductionJobID(item.Target.ID), now)
			return err
		case action.TypeRespawnResource:
			if r.resources == nil {
				return nil
			}
			_, err := r.resources.Tick(ctx, now, 1)
			return err
		case action.TypeRegrowForest:
			if r.forests == nil {
				return nil
			}
			return r.forests.HandleRegrowthAction(ctx, item, now)
		case action.TypeDetonateWeapon:
			if r.combat == nil { return nil }
			if err := r.combat.ResolveWeapon(ctx, item); err != nil { return err }
			return r.actions.MarkDone(ctx, item.ID, now)
		case action.TypeResolveRaid:
			if r.raids == nil { return nil }
			return r.raids.Resolve(ctx, item, now)
		default:
			return nil
		}
	}
	if r.uow != nil {
		return r.uow.Do(ctx, run)
	}
	return run(ctx)
}

type skipActionQueueKey struct{}

func WithoutActionQueue(ctx context.Context) context.Context {
	return context.WithValue(ctx, skipActionQueueKey{}, true)
}

func backoff(attempts int) time.Duration {
	delay := time.Duration(1+attempts) * time.Second
	if delay > 30*time.Second {
		return 30 * time.Second
	}
	return delay
}
