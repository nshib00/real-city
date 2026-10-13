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

	db := openPostgres(cfg, log)
	if db != nil {
		defer db.Close()
	}
	playerRepo := buildPlayerStore(db)
	worldRepo := buildWorldStore(db)
	buildingRepo := buildBuildingStore(db)
	economyRepo := buildEconomyStore(db)
	monsterRepo := buildMonsterStore(db)
	actionRepo := buildActionStore(db)
	outboxRepo := buildOutboxStore(db)
	uow := buildUnitOfWork(db)
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

func openPostgres(cfg config.Config, log *slog.Logger) *postgresadapter.DB {
	if cfg.Postgres.DSN == "" {
		log.Info("storage.memory", "event", "storage.memory")
		return nil
	}
	db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
	if err != nil {
		log.Warn("postgres.unavailable_fallback_memory", "event", "postgres.unavailable_fallback_memory", logger.ErrorAttr(err))
		return nil
	}
	log.Info("postgres.connected", "event", "postgres.connected")
	return db
}

func buildPlayerStore(db *postgresadapter.DB) service.PlayerRepository {
	if db != nil {
		return postgresadapter.NewPlayerRepo(db.Pool())
	}
	return memory.NewPlayerRepo()
}

func buildMonsterStore(db *postgresadapter.DB) service.MonsterRepository {
	if db != nil {
		return postgresadapter.NewMonsterRepo(db.Pool())
	}
	return memory.NewMonsterRepo()
}

func buildWorldStore(db *postgresadapter.DB) service.WorldRepository {
	if db != nil {
		return postgresadapter.NewWorldRepo(db.Pool())
	}
	return memory.NewWorldRepo()
}

func buildBuildingStore(db *postgresadapter.DB) service.BuildingRepository {
	if db != nil {
		return postgresadapter.NewBuildingRepo(db.Pool())
	}
	return memory.NewBuildingRepo()
}

func buildEconomyStore(db *postgresadapter.DB) service.EconomyRepository {
	if db != nil {
		return postgresadapter.NewEconomyRepo(db.Pool())
	}
	return memory.NewEconomyRepo()
}

func buildActionStore(db *postgresadapter.DB) service.ActionRepository {
	if db != nil {
		return postgresadapter.NewActionRepo(db.Pool())
	}
	return memory.NewActionRepo()
}

func buildOutboxStore(db *postgresadapter.DB) service.OutboxRepository {
	if db != nil {
		return postgresadapter.NewOutboxRepo(db.Pool())
	}
	return memory.NewOutboxRepo()
}

func buildUnitOfWork(db *postgresadapter.DB) service.UnitOfWork {
	if db != nil {
		return postgresadapter.NewUnitOfWork(db.Pool())
	}
	return nil
}
