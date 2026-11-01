package main

import (
	"context"
	"database/sql"
	"fmt"
	"log/slog"
	"net/http"
	"time"

	httpadapter "real-city/backend/internal/adapter/http"
	httpmiddleware "real-city/backend/internal/adapter/http/middleware"
	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/adapter/memory"
	postgresadapter "real-city/backend/internal/adapter/postgres"
	wsadapter "real-city/backend/internal/adapter/ws"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service"
	"real-city/backend/internal/worker"
	"real-city/backend/internal/worker/simulation"
	"real-city/backend/pkg/config"
)

type app struct {
	cfg      config.Config
	log      *slog.Logger
	db       *postgresadapter.DB
	server   *http.Server
	realtime *wsadapter.Gateway
	sim      *simulation.Runner
	outbox   *worker.OutboxDispatcher
}

func newApp(cfg config.Config, log *slog.Logger) (*app, error) {
	db, err := openPostgres(cfg, log)
	if err != nil {
		return nil, err
	}
	var dbPool *sql.DB
	if db != nil {
		dbPool = db.Pool()
	}
	var idempotencyStore httpmiddleware.IdempotencyStore
	if dbPool != nil {
		idempotencyStore = postgresadapter.NewIdempotencyStore(dbPool)
	}
	playerRepo, sessionStore := buildStores(db)
	worldRepo := buildWorldStore(db)
	buildingRepo := buildBuildingStore(db)
	economyRepo := buildEconomyStore(db)
	monsterRepo := buildMonsterStore(db)
	var socialRepo interface {
		service.AllianceRepository
		service.ChatRepository
		service.MarketRepository
	}
	if dbPool != nil {
		socialRepo = postgresadapter.NewSocialRepo(dbPool)
	} else {
		socialRepo = memory.NewSocialRepo()
	}
	tokenManager := jwtadapter.NewManager(cfg.Session.Secret, cfg.Session.AccessTTL, cfg.Session.RefreshTTL)
	authService := service.NewAuthService(playerRepo, sessionStore, tokenManager, log)
	playerService := service.NewPlayerService(playerRepo, sessionStore, log)
	playerService.SetProfileSources(buildingRepo, socialRepo)
	experienceService := service.NewExperienceService(playerRepo, log)
	worldService := service.NewWorldService(worldRepo, log)
	buildingService := service.NewBuildingService(buildingRepo, worldRepo, log)
	buildingService.SetPvPProtection(playerRepo)
	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	economyService.SetPlayers(playerRepo)
	resourceService := service.NewResourceService(economyRepo, economyService, log)
	resourceService.SetOilWorld(worldRepo, buildingRepo)
	buildingService.SetResources(resourceService)
	productionService := service.NewProductionService(economyRepo, economyService, log)
	monsterService := service.NewMonsterService(monsterRepo, log)
	monsterService.SetEconomy(economyService)
	combatService := service.NewCombatService(monsterService, log)
	combatService.SetBuildingService(buildingService)
	threatService := service.NewThreatService(monsterRepo)
	allianceService := service.NewAllianceService(socialRepo, economyService, log)
	buildingService.SetAllianceBenefits(allianceService)
	resourceService.SetAllianceBenefits(allianceService)
	chatService := service.NewChatService(socialRepo, socialRepo, log)
	chatService.SetBuildings(buildingRepo)
	marketService := service.NewMarketService(socialRepo, economyService, log)
	actionRepo := buildActionStore(db)
	outboxRepo := buildOutboxStore(db)
	uow := buildUnitOfWork(db)
	economyService.SetUnitOfWork(uow)
	productionService.SetUnitOfWork(uow)
	marketService.SetUnitOfWork(uow)
	chatService.SetUnitOfWork(uow)
	allianceService.SetUnitOfWork(uow)
	combatService.SetWeaponDependencies(economyRepo, actionRepo, uow)
	combatService.SetPvPDependencies(buildingRepo, worldRepo, resourceService)
	fieldService := service.NewFieldService(economyService, buildingRepo)
	populationService := service.NewPopulationService(economyService)
	forestService := service.NewForestService(worldRepo, economyService, log)
	eventBus := service.NewEventBus(128)
	marketService.SetEventBus(eventBus)
	allianceService.SetEventBus(eventBus)
	chatService.SetEventBus(eventBus)
	playerService.SetEventBus(eventBus)
	buildingService.SetEconomy(economyService)
	buildingService.SetRepairUnitOfWork(uow)
	buildingService.SetActionQueue(actionRepo)
	buildingService.SetMonsters(monsterRepo)
	economyService.SetEventBus(eventBus)
	buildingService.SetEventBus(eventBus)
	forestService.SetEventBus(eventBus)
	resourceService.SetEventBus(eventBus)
	resourceService.SetActionQueue(actionRepo)
	resourceService.SetExperience(experienceService)
	forestService.SetActionQueue(actionRepo)
	forestService.SetBuildingRepository(buildingRepo)
	forestService.SetExperience(experienceService)
	buildingService.SetExperience(experienceService)
	fieldService.SetExperience(experienceService)
	productionService.SetExperience(experienceService)
	monsterService.SetExperience(experienceService)
	productionService.SetEventBus(eventBus)
	productionService.SetActionQueue(actionRepo)
	productionService.SetBuildings(buildingRepo)
	productionService.SetResources(resourceService)
	monsterService.SetEventBus(eventBus)
	var simulationRunner *simulation.Runner
	outboxDispatcher := worker.NewOutboxDispatcher(outboxRepo, eventBus, log, cfg.Simulation)
	if cfg.Simulation.Embedded {
		simulationRunner = simulation.NewRunner(actionRepo, uow, buildingService, productionService, resourceService, log, cfg.Simulation)
		simulationRunner.SetForestService(forestService)
		simulationRunner.SetMonsterSpawner(simulation.NewMonsterSpawner(monsterService, monsterRepo, buildingRepo, worldRepo, log))
		monsterAI := simulation.NewMonsterAI(monsterRepo, buildingRepo, worldRepo, eventBus, log)
		monsterAI.SetUnitOfWork(uow)
		monsterAI.SetExperience(experienceService)
		monsterAI.SetBuildingService(buildingService)
		monsterAI.SetMoveInterval(cfg.Simulation.TickInterval)
		simulationRunner.SetMonsterAI(monsterAI)
		simulationRunner.SetCannonService(service.NewCannonService(buildingRepo, monsterRepo, economyRepo, worldRepo, uow, monsterService, economyService, eventBus, log))
		simulationRunner.SetCombatService(combatService)
	}
	realtimeGateway := wsadapter.NewGateway(tokenManager, eventBus, log)
	realtimeGateway.SetAccessValidator(playerService)

	return &app{
		cfg:      cfg,
		log:      log,
		db:       db,
		realtime: realtimeGateway,
		sim:      simulationRunner,
		outbox:   outboxDispatcher,
		server: &http.Server{
			Handler:      httpadapter.NewRouter(log, httpadapter.RouterDeps{AppEnv: cfg.AppEnv, AllowedOrigins: cfg.Server.AllowedOrigins, Auth: authService, Players: playerService, Worlds: worldService, Forests: forestService, Buildings: buildingService, Economy: economyService, Resources: resourceService, Production: productionService, Fields: fieldService, Population: populationService, Monsters: monsterService, Combat: combatService, Threats: threatService, Alliances: allianceService, Chat: chatService, Market: marketService, Tokens: tokenManager, Realtime: realtimeGateway, DBPool: dbPool, Idempotency: idempotencyStore}),
			Addr:         cfg.Server.Addr,
			ReadTimeout:  cfg.Server.ReadTimeout,
			WriteTimeout: cfg.Server.WriteTimeout,
		},
	}, nil
}

func openPostgres(cfg config.Config, log *slog.Logger) (*postgresadapter.DB, error) {
	if cfg.Postgres.DSN == "" {
		if cfg.AppEnv == "production" {
			return nil, fmt.Errorf("production requires POSTGRES_DSN")
		}
		log.Info("storage.memory", "event", "storage.memory")
		return nil, nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	db, err := postgresadapter.Open(ctx, cfg.Postgres.Driver, cfg.Postgres.DSN)
	if err != nil {
		return nil, fmt.Errorf("configured PostgreSQL unavailable: %w", err)
	}
	log.Info("postgres.connected", "event", "postgres.connected")
	return db, nil
}

func buildMonsterStore(db *postgresadapter.DB) service.MonsterRepository {
	if db != nil {
		return postgresadapter.NewMonsterRepo(db.Pool())
	}
	return memory.NewMonsterRepo()
}

func buildStores(db *postgresadapter.DB) (service.PlayerRepository, service.SessionStore) {
	if db != nil {
		return postgresadapter.NewPlayerRepo(db.Pool()), postgresadapter.NewSessionRepo(db.Pool())
	}
	return memory.NewPlayerRepo(), memory.NewSessionStore()
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

func (a *app) run(ctx context.Context) error {
	if !a.cfg.Simulation.Embedded && a.db == nil {
		return fmt.Errorf("standalone simulation requires a shared PostgreSQL connection")
	}
	if a.db != nil {
		defer a.db.Close()
		var storedVersion int
		if err := a.db.Pool().QueryRowContext(ctx, `SELECT version FROM game_balance_version WHERE singleton=true`).Scan(&storedVersion); err != nil {
			return err
		}
		if storedVersion != catalog.BalanceVersion {
			return fmt.Errorf("balance version mismatch: database=%d backend=%d; apply migrations before starting", storedVersion, catalog.BalanceVersion)
		}
	}
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	if a.db != nil {
		go postgresadapter.RunQueueSampler(runCtx, a.db.Pool(), a.log)
	}
	if a.sim != nil {
		observability.EnableSimulation()
	}
	errCh := make(chan error, 3)
	if a.sim != nil {
		go func() {
			a.log.Info("simulation.worker.start", "event", "simulation.worker.start")
			errCh <- a.sim.Run(runCtx)
		}()
	}
	if a.outbox != nil {
		go func() {
			a.log.Info("outbox.worker.start", "event", "outbox.worker.start")
			errCh <- a.outbox.Run(runCtx)
		}()
	}
	go func() {
		a.log.Info("http.server.start", "event", "http.server.start", "addr", a.cfg.Server.Addr)
		errCh <- a.server.ListenAndServe()
	}()

	select {
	case <-ctx.Done():
		cancel()
		if a.realtime != nil {
			a.realtime.Shutdown()
		}
		shutdownCtx, cancel := context.WithTimeout(context.Background(), a.cfg.Server.ShutdownTimeout)
		defer cancel()
		if err := a.server.Shutdown(shutdownCtx); err != nil {
			return err
		}
		return nil
	case err := <-errCh:
		if err == http.ErrServerClosed || err == context.Canceled {
			return nil
		}
		return err
	}
}
