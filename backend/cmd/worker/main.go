package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"real-city/backend/internal/adapter/memory"
	postgresadapter "real-city/backend/internal/adapter/postgres"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service"
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
	if err := run(ctx, cfg, log); err != nil {
		log.Error("worker.failed", "event", "worker.failed", logger.ErrorAttr(err))
		os.Exit(1)
	}
}

func run(ctx context.Context, cfg config.Config, log *slog.Logger) error {
	db := openPostgres(cfg, log)
	if db == nil {
		return errors.New("standalone worker requires a shared PostgreSQL connection")
	}
	dbPool := db.Pool()
	defer db.Close()
	runCtx, cancelRun := context.WithCancel(ctx)
	defer cancelRun()
	playerRepo := buildPlayerStore(db)
	experienceService := service.NewExperienceService(playerRepo, log)
	worldRepo := buildWorldStore(db)
	buildingRepo := buildBuildingStore(db)
	economyRepo := buildEconomyStore(db)
	monsterRepo := buildMonsterStore(db)
	actionRepo := buildActionStore(db)
	outboxRepo := buildOutboxStore(db)
	uow := buildUnitOfWork(db)
	eventBus := service.NewEventBus(128)
	eventBus.SetForwarder(service.NewOutboxForwarder(outboxRepo))

	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	economyService.SetPlayers(playerRepo)
	buildingService := service.NewBuildingService(buildingRepo, worldRepo, log)
	buildingService.SetMonsters(monsterRepo)
	resourceService := service.NewResourceService(economyRepo, economyService, log)
	resourceService.SetOilWorld(worldRepo, buildingRepo)
	buildingService.SetResources(resourceService)
	productionService := service.NewProductionService(economyRepo, economyService, log)
	forestService := service.NewForestService(worldRepo, economyService, log)
	monsterService := service.NewMonsterService(monsterRepo, log)
	monsterService.SetEconomy(economyService)
	combatService := service.NewCombatService(monsterService, log)
	combatService.SetWeaponDependencies(economyRepo, actionRepo, uow)
	buildingService.SetEconomy(economyService)
	buildingService.SetActionQueue(actionRepo)
	buildingService.SetEventBus(eventBus)
	resourceService.SetEventBus(eventBus)
	resourceService.SetActionQueue(actionRepo)
	resourceService.SetExperience(experienceService)
	forestService.SetEventBus(eventBus)
	forestService.SetActionQueue(actionRepo)
	forestService.SetBuildingRepository(buildingRepo)
	forestService.SetExperience(experienceService)
	buildingService.SetExperience(experienceService)
	productionService.SetExperience(experienceService)
	monsterService.SetExperience(experienceService)
	productionService.SetEventBus(eventBus)
	productionService.SetActionQueue(actionRepo)
	productionService.SetBuildings(buildingRepo)
	productionService.SetResources(resourceService)
	economyService.SetEventBus(eventBus)

	sim := simulation.NewRunner(actionRepo, uow, buildingService, productionService, resourceService, log, cfg.Simulation)
	sim.SetForestService(forestService)
	sim.SetMonsterSpawner(simulation.NewMonsterSpawner(monsterService, monsterRepo, buildingRepo, worldRepo, log))
	monsterAI := simulation.NewMonsterAI(monsterRepo, buildingRepo, worldRepo, eventBus, log)
	monsterAI.SetUnitOfWork(uow)
	monsterAI.SetExperience(experienceService)
	monsterAI.SetMoveInterval(cfg.Simulation.TickInterval)
	sim.SetMonsterAI(monsterAI)
	sim.SetCannonService(service.NewCannonService(buildingRepo, monsterRepo, economyRepo, worldRepo, uow, monsterService, economyService, eventBus, log))
	sim.SetCombatService(combatService)
	raidService := service.NewRaidService(buildingRepo, actionRepo, log)
	raidService.SetResources(resourceService)
	raidService.SetEventBus(eventBus)
	sim.SetRaidService(raidService)
	observability.EnableSimulation()
	go postgresadapter.RunQueueSampler(runCtx, dbPool, log)

	metricsServer := &http.Server{Addr: cfg.Observability.MetricsAddr, Handler: observability.WorkerHandler(dbPool), ReadHeaderTimeout: 5 * time.Second}
	errCh := make(chan error, 2)
	go func() { errCh <- sim.Run(runCtx) }()
	go func() { errCh <- metricsServer.ListenAndServe() }()

	var runErr error
	select {
	case <-ctx.Done():
	case err := <-errCh:
		if err != nil && err != context.Canceled && err != http.ErrServerClosed {
			runErr = err
		}
	}
	cancelRun()
	shutdownCtx, cancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
	defer cancel()
	if err := metricsServer.Shutdown(shutdownCtx); err != nil {
		log.Error("worker.metrics.shutdown_failed", "event", "worker.metrics.shutdown_failed", logger.ErrorAttr(err))
		if runErr == nil {
			runErr = err
		}
	}
	return runErr
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
