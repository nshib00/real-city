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
	server   *http.Server
	realtime *wsadapter.Gateway
	sim      *simulation.Runner
	outbox   *worker.OutboxDispatcher
}

func newApp(cfg config.Config, log *slog.Logger) *app {
	playerRepo, sessionStore := buildStores(cfg, log)
	worldRepo := buildWorldStore(cfg, log)
	buildingRepo := buildBuildingStore(cfg, log)
	economyRepo := buildEconomyStore(cfg, log)
	monsterRepo := buildMonsterStore(cfg, log)
	socialRepo := memory.NewSocialRepo()
	tokenManager := jwtadapter.NewManager(cfg.Session.Secret, cfg.Session.AccessTTL, cfg.Session.RefreshTTL)
	authService := service.NewAuthService(playerRepo, sessionStore, tokenManager, log)
	playerService := service.NewPlayerService(playerRepo, sessionStore, log)
	worldService := service.NewWorldService(worldRepo, log)
	buildingService := service.NewBuildingService(buildingRepo, worldRepo, log)
	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	resourceService := service.NewResourceService(economyRepo, economyService, log)
	productionService := service.NewProductionService(economyRepo, economyService, log)
	monsterService := service.NewMonsterService(monsterRepo, log)
	combatService := service.NewCombatService(monsterService, log)
	threatService := service.NewThreatService(monsterRepo)
	allianceService := service.NewAllianceService(socialRepo, economyService, log)
	chatService := service.NewChatService(socialRepo, socialRepo, log)
	marketService := service.NewMarketService(socialRepo, economyService, log)
	actionRepo := buildActionStore(cfg, log)
	outboxRepo := buildOutboxStore(cfg, log)
	uow := buildUnitOfWork(cfg, log)
	fieldService := service.NewFieldService(economyService)
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
	productionService.SetEventBus(eventBus)
	productionService.SetActionQueue(actionRepo)
	monsterService.SetEventBus(eventBus)
	simulationRunner := simulation.NewRunner(actionRepo, uow, buildingService, productionService, resourceService, log, cfg.Simulation)
	simulationRunner.SetMonsterAI(simulation.NewMonsterAI(monsterRepo, buildingRepo, eventBus, log))
	economyService.SetCatchUp(func(ctx context.Context, playerID player.ID) error {
		return simulationRunner.CatchUp(ctx, string(playerID))
	})
	outboxDispatcher := worker.NewOutboxDispatcher(outboxRepo, eventBus, log, cfg.Simulation)
	realtimeGateway := wsadapter.NewGateway(tokenManager, eventBus, log)

	return &app{
		cfg:      cfg,
		log:      log,
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

func buildStores(cfg config.Config, log *slog.Logger) (service.PlayerRepository, service.SessionStore) {
	if cfg.Postgres.DSN != "" {
		db, err := postgresadapter.Open(context.Background(), cfg.Postgres.Driver, cfg.Postgres.DSN)
		if err == nil {
			log.Info("postgres.connected", "event", "postgres.connected")
			return postgresadapter.NewPlayerRepo(db.Pool()), postgresadapter.NewSessionRepo(db.Pool())
		}
		log.Warn("postgres.unavailable_fallback_memory", "event", "postgres.unavailable_fallback_memory", logger.ErrorAttr(err))
	}
	log.Info("storage.memory", "event", "storage.memory")
	return memory.NewPlayerRepo(), memory.NewSessionStore()
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

func (a *app) run(ctx context.Context) error {
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
