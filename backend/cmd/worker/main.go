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

	playerRepo := buildPlayerStore(cfg, log)
	worldRepo := buildWorldStore(cfg, log)
	buildingRepo := buildBuildingStore(cfg, log)
	economyRepo := buildEconomyStore(cfg, log)
	monsterRepo := buildMonsterStore(cfg, log)
	actionRepo := buildActionStore(cfg, log)
	outboxRepo := buildOutboxStore(cfg, log)
	uow := buildUnitOfWork(cfg, log)
	eventBus := service.NewEventBus(128)

	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	economyService.SetPlayers(playerRepo)
	buildingService := service.NewBuildingService(buildingRepo, worldRepo, log)
	buildingService.SetMonsters(monsterRepo)
	resourceService := service.NewResourceService(economyRepo, economyService, log)
	productionService := service.NewProductionService(economyRepo, economyService, log)
	forestService := service.NewForestService(worldRepo, economyService, log)
	monsterService := service.NewMonsterService(monsterRepo, log)
	monsterService.SetEconomy(economyService)
	buildingService.SetEconomy(economyService)
	buildingService.SetActionQueue(actionRepo)
	buildingService.SetEventBus(eventBus)
	resourceService.SetEventBus(eventBus)
	resourceService.SetActionQueue(actionRepo)
	forestService.SetEventBus(eventBus)
	forestService.SetActionQueue(actionRepo)
	forestService.SetBuildingRepository(buildingRepo)
	productionService.SetEventBus(eventBus)
	productionService.SetActionQueue(actionRepo)
	productionService.SetBuildings(buildingRepo)
	economyService.SetEventBus(eventBus)

	sim := simulation.NewRunner(actionRepo, uow, buildingService, productionService, resourceService, log, cfg.Simulation)
	sim.SetForestService(forestService)
	sim.SetMonsterSpawner(simulation.NewMonsterSpawner(monsterService, monsterRepo, buildingRepo, worldRepo, log))
	sim.SetMonsterAI(simulation.NewMonsterAI(monsterRepo, buildingRepo, worldRepo, eventBus, log))
	dispatcher := worker.NewOutboxDispatcher(outboxRepo, eventBus, log, cfg.Simulation)

	errCh := make(chan error, 2)
	go func() { errCh <- sim.Run(ctx) }()
	go func() { errCh <- dispatcher.Run(ctx) }()

	if err := <-errCh; err != nil && err != context.Canceled {
		log.Error("worker.failed", "event", "worker.failed", logger.ErrorAttr(err))
		os.Exit(1)
	}
}

func buildPlayerStore(cfg config.Config, log *slog.Logger) service.PlayerRepository {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewPlayerRepo(db.Pool())
		}
		log.Warn("postgres.players_unavailable_fallback_memory", "event", "postgres.players_unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	return memory.NewPlayerRepo()
}

func buildMonsterStore(cfg config.Config, log *slog.Logger) service.MonsterRepository {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			return postgresadapter.NewMonsterRepo(db.Pool())
		}
		log.Warn("postgres.monsters_unavailable_fallback_memory", "event", "postgres.monsters_unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	return memory.NewMonsterRepo()
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
