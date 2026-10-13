package main

import (
	"context"
	"log/slog"
	"net/http"

	httpadapter "real-city/backend/internal/adapter/http"
	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/adapter/memory"
	postgresadapter "real-city/backend/internal/adapter/postgres"
	wsadapter "real-city/backend/internal/adapter/ws"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"real-city/backend/internal/worker"
	"real-city/backend/internal/worker/simulation"
	"real-city/backend/pkg/config"
	"real-city/backend/pkg/logger"
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

func newApp(cfg config.Config, log *slog.Logger) *app {
	db := openPostgres(cfg, log)
	playerRepo, sessionStore := buildStores(db)
	worldRepo := buildWorldStore(db)
	buildingRepo := buildBuildingStore(db)
	economyRepo := buildEconomyStore(db)
	monsterRepo := buildMonsterStore(db)
	socialRepo := memory.NewSocialRepo()
	tokenManager := jwtadapter.NewManager(cfg.Session.Secret, cfg.Session.AccessTTL, cfg.Session.RefreshTTL)
	authService := service.NewAuthService(playerRepo, sessionStore, tokenManager, log)
	playerService := service.NewPlayerService(playerRepo, sessionStore, log)
	worldService := service.NewWorldService(worldRepo, log)
	buildingService := service.NewBuildingService(buildingRepo, worldRepo, log)
	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	economyService.SetPlayers(playerRepo)
	resourceService := service.NewResourceService(economyRepo, economyService, log)
	productionService := service.NewProductionService(economyRepo, economyService, log)
	monsterService := service.NewMonsterService(monsterRepo, log)
	monsterService.SetEconomy(economyService)
	combatService := service.NewCombatService(monsterService, log)
	threatService := service.NewThreatService(monsterRepo)
	allianceService := service.NewAllianceService(socialRepo, economyService, log)
	chatService := service.NewChatService(socialRepo, socialRepo, log)
	marketService := service.NewMarketService(socialRepo, economyService, log)
	actionRepo := buildActionStore(db)
	outboxRepo := buildOutboxStore(db)
	uow := buildUnitOfWork(db)
	fieldService := service.NewFieldService(economyService, buildingRepo)
	populationService := service.NewPopulationService(economyService)
	forestService := service.NewForestService(worldRepo, economyService, log)
	eventBus := service.NewEventBus(128)
	buildingService.SetEconomy(economyService)
	buildingService.SetActionQueue(actionRepo)
	buildingService.SetMonsters(monsterRepo)
	economyService.SetEventBus(eventBus)
	buildingService.SetEventBus(eventBus)
	forestService.SetEventBus(eventBus)
	resourceService.SetEventBus(eventBus)
	resourceService.SetActionQueue(actionRepo)
	forestService.SetActionQueue(actionRepo)
	forestService.SetBuildingRepository(buildingRepo)
	productionService.SetEventBus(eventBus)
	productionService.SetActionQueue(actionRepo)
	productionService.SetBuildings(buildingRepo)
	monsterService.SetEventBus(eventBus)
	simulationRunner := simulation.NewRunner(actionRepo, uow, buildingService, productionService, resourceService, log, cfg.Simulation)
	simulationRunner.SetForestService(forestService)
	simulationRunner.SetMonsterSpawner(simulation.NewMonsterSpawner(monsterService, monsterRepo, buildingRepo, worldRepo, log))
	simulationRunner.SetMonsterAI(simulation.NewMonsterAI(monsterRepo, buildingRepo, worldRepo, eventBus, log))
	economyService.SetCatchUp(func(ctx context.Context, playerID player.ID) error {
		return simulationRunner.CatchUp(ctx, string(playerID))
	})
	outboxDispatcher := worker.NewOutboxDispatcher(outboxRepo, eventBus, log, cfg.Simulation)
	realtimeGateway := wsadapter.NewGateway(tokenManager, eventBus, log)

	return &app{
		cfg:      cfg,
		log:      log,
		db:       db,
		realtime: realtimeGateway,
		sim:      simulationRunner,
		outbox:   outboxDispatcher,
		server: &http.Server{
			Addr:         cfg.Server.Addr,
			Handler:      httpadapter.NewRouter(log, httpadapter.RouterDeps{Auth: authService, Players: playerService, Worlds: worldService, Forests: forestService, Buildings: buildingService, Economy: economyService, Resources: resourceService, Production: productionService, Fields: fieldService, Population: populationService, Monsters: monsterService, Combat: combatService, Threats: threatService, Alliances: allianceService, Chat: chatService, Market: marketService, Tokens: tokenManager, Realtime: realtimeGateway}),
			ReadTimeout:  cfg.Server.ReadTimeout,
			WriteTimeout: cfg.Server.WriteTimeout,
		},
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
	if a.db != nil {
		defer a.db.Close()
	}
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()
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
