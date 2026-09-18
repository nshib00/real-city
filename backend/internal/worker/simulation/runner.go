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
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

type Runner struct {
	actions    service.ActionRepository
	uow        service.UnitOfWork
	buildings  *service.BuildingService
	production *service.ProductionService
	resources  *service.ResourceService
	monsters   *MonsterAI
	log        *slog.Logger
	cfg        config.SimulationConfig
	now        func() time.Time
}

type TickResult struct {
	ActionsProcessed    int
	BuildingsCompleted  int
	ProductionCompleted int
	ResourcesRespawned  int
	MonstersProcessed   int
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

func (r *Runner) Run(ctx context.Context) error {
	ticker := time.NewTicker(r.cfg.TickInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			_, _ = r.Tick(ctx)
		}
	}
}

func (r *Runner) Tick(ctx context.Context) (result TickResult, err error) {
	start := r.now()
	r.log.Info("simulation.tick.start", "event", "simulation.tick.start")
	defer func() {
		if recovered := recover(); recovered != nil {
			result.Failures++
			err = errors.New("simulation tick panic")
			r.log.Error("simulation.tick.panic", "event", "simulation.tick.panic", "panic", recovered, "stack", string(debug.Stack()))
		}
		duration := r.now().Sub(start)
		level := slog.LevelInfo
		if duration > r.cfg.TickInterval {
			level = slog.LevelWarn
		}
		r.log.Log(ctx, level, "simulation.tick.finish", "event", "simulation.tick.finish", "duration_ms", duration.Milliseconds(), "actions", result.ActionsProcessed, "buildings", result.BuildingsCompleted, "production", result.ProductionCompleted, "resources", result.ResourcesRespawned, "monsters", result.MonstersProcessed, "failures", result.Failures)
	}()

	now := r.now()
	if r.actions != nil {
		processed, failures, err := r.processActions(ctx, now)
		result.ActionsProcessed = processed
		result.Failures += failures
		if err != nil {
			return result, err
		}
	}
	if r.buildings != nil {
		result.BuildingsCompleted, err = r.buildings.CompleteDue(ctx, now, r.cfg.BatchSize)
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.production != nil {
		result.ProductionCompleted, err = r.production.CompleteDue(ctx, now, r.cfg.BatchSize)
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.resources != nil {
		result.ResourcesRespawned, err = r.resources.Tick(ctx, now, r.cfg.BatchSize)
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	if r.monsters != nil {
		result.MonstersProcessed, err = r.monsters.Tick(ctx, now, r.cfg.BatchSize)
		if err != nil {
			result.Failures++
			return result, err
		}
	}
	return result, nil
}

func (r *Runner) CatchUp(ctx context.Context, playerID string) error {
	if r.cfg.CatchUpLimit <= 0 {
		return nil
	}
	_, err := r.Tick(WithoutActionQueue(ctx))
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
	failures := 0
	for _, item := range actions {
		err := r.handleAction(ctx, item, now)
		if err != nil {
			failures++
			retryAt := now.Add(backoff(item.Attempts))
			_ = r.actions.MarkFailed(ctx, item.ID, err.Error(), retryAt, now)
			r.log.Warn("simulation.action.failed", "event", "simulation.action.failed", "action_id", item.ID, "action_type", item.Type, "attempts", item.Attempts+1, "retry_at", retryAt, "error", err.Error())
			continue
		}
		if err := r.actions.MarkDone(ctx, item.ID, now); err != nil {
			return len(actions), failures + 1, err
		}
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
			_, _, err := r.production.CompleteAt(ctx, player.ID(item.Actor.ID), economy.ProductionJobID(item.Target.ID), now)
			return err
		case action.TypeRespawnResource:
			if r.resources == nil {
				return nil
			}
			_, err := r.resources.Tick(ctx, now, 1)
			return err
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
