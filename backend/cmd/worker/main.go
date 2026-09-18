package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"real-city/backend/internal/adapter/memory"
	postgresadapter "real-city/backend/internal/adapter/postgres"
	"real-city/backend/internal/service"
	"real-city/backend/internal/worker"
	"real-city/backend/internal/worker/simulation"
	"real-city/backend/pkg/config"
	"real-city/backend/pkg/logger"
)

func main() {
	cfg := config.Load()
	log := logger.New(cfg.AppEnv, cfg.Observability.LogLevel)
	slog.SetDefault(log)

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	worldRepo := buildWorldStore(cfg, log)
	buildingRepo := buildBuildingStore(cfg, log)
	economyRepo := buildEconomyStore(cfg, log)
	actionRepo := buildActionStore(cfg, log)
	outboxRepo := buildOutboxStore(cfg, log)
	uow := buildUnitOfWork(cfg, log)
	eventBus := service.NewEventBus(128)

	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	buildingService := service.NewBuildingService(buildingRepo, worldRepo, log)
	resourceService := service.NewResourceService(economyRepo, economyService, log)
	productionService := service.NewProductionService(economyRepo, economyService, log)
	buildingService.SetEconomy(economyService)
	buildingService.SetActionQueue(actionRepo)
	buildingService.SetEventBus(eventBus)
	resourceService.SetEventBus(eventBus)
	resourceService.SetActionQueue(actionRepo)
	productionService.SetEventBus(eventBus)
	productionService.SetActionQueue(actionRepo)
	economyService.SetEventBus(eventBus)

	sim := simulation.NewRunner(actionRepo, uow, buildingService, productionService, resourceService, log, cfg.Simulation)
	dispatcher := worker.NewOutboxDispatcher(outboxRepo, eventBus, log, cfg.Simulation)

	errCh := make(chan error, 2)
	go func() { errCh <- sim.Run(ctx) }()
	go func() { errCh <- dispatcher.Run(ctx) }()

	if err := <-errCh; err != nil && err != context.Canceled {
		log.Error("worker.failed", "event", "worker.failed", logger.ErrorAttr(err))
		os.Exit(1)
	}
}

func buildWorldStore(cfg config.Config, log *slog.Logger) service.WorldRepository {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewWorldRepo(db.Pool())
		}
		log.Warn("postgres.world_unavailable_fallback_memory", "event", "postgres.world_unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	return memory.NewWorldRepo()
}

func buildBuildingStore(cfg config.Config, log *slog.Logger) service.BuildingRepository {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewBuildingRepo(db.Pool())
		}
		log.Warn("postgres.buildings_unavailable_fallback_memory", "event", "postgres.buildings_unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	return memory.NewBuildingRepo()
}

func buildEconomyStore(cfg config.Config, log *slog.Logger) service.EconomyRepository {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewEconomyRepo(db.Pool())
		}
		log.Warn("postgres.economy_unavailable_fallback_memory", "event", "postgres.economy_unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	return memory.NewEconomyRepo()
}

func buildActionStore(cfg config.Config, log *slog.Logger) service.ActionRepository {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewActionRepo(db.Pool())
		}
		log.Warn("postgres.actions_unavailable_fallback_memory", "event", "postgres.actions_unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	return memory.NewActionRepo()
}

func buildOutboxStore(cfg config.Config, log *slog.Logger) service.OutboxRepository {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewOutboxRepo(db.Pool())
		}
		log.Warn("postgres.outbox_unavailable_fallback_memory", "event", "postgres.outbox_unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	return memory.NewOutboxRepo()
}

func buildUnitOfWork(cfg config.Config, log *slog.Logger) service.UnitOfWork {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewUnitOfWork(db.Pool())
		}
		log.Warn("postgres.uow_unavailable", "event", "postgres.uow_unavailable", logger.ErrorAttr(err))
	}
	return nil
}
