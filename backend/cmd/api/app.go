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
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
	"real-city/backend/pkg/logger"
)

type app struct {
	cfg      config.Config
	log      *slog.Logger
	server   *http.Server
	realtime *wsadapter.Gateway
}

func newApp(cfg config.Config, log *slog.Logger) *app {
	playerRepo, sessionStore := buildStores(cfg, log)
	worldRepo := buildWorldStore(cfg, log)
	buildingRepo := buildBuildingStore(cfg, log)
	economyRepo := buildEconomyStore(cfg, log)
	tokenManager := jwtadapter.NewManager(cfg.Session.Secret, cfg.Session.AccessTTL, cfg.Session.RefreshTTL)
	authService := service.NewAuthService(playerRepo, sessionStore, tokenManager, log)
	playerService := service.NewPlayerService(playerRepo, sessionStore, log)
	worldService := service.NewWorldService(worldRepo, log)
	buildingService := service.NewBuildingService(buildingRepo, worldRepo, log)
	economyService := service.NewEconomyService(economyRepo, buildingRepo, log)
	resourceService := service.NewResourceService(economyRepo, economyService, log)
	productionService := service.NewProductionService(economyRepo, economyService, log)
	fieldService := service.NewFieldService(economyService)
	populationService := service.NewPopulationService(economyService)
	forestService := service.NewForestService(worldRepo, economyService, log)
	eventBus := service.NewEventBus(128)
	buildingService.SetEconomy(economyService)
	buildingService.SetEventBus(eventBus)
	forestService.SetEventBus(eventBus)
	resourceService.SetEventBus(eventBus)
	realtimeGateway := wsadapter.NewGateway(tokenManager, eventBus, log)

	return &app{
		cfg:      cfg,
		log:      log,
		realtime: realtimeGateway,
		server: &http.Server{
			Addr:         cfg.Server.Addr,
			Handler:      httpadapter.NewRouter(log, httpadapter.RouterDeps{Auth: authService, Players: playerService, Worlds: worldService, Forests: forestService, Buildings: buildingService, Economy: economyService, Resources: resourceService, Production: productionService, Fields: fieldService, Population: populationService, Tokens: tokenManager, Realtime: realtimeGateway}),
			ReadTimeout:  cfg.Server.ReadTimeout,
			WriteTimeout: cfg.Server.WriteTimeout,
		},
	}
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

func (a *app) run(ctx context.Context) error {
	errCh := make(chan error, 1)
	go func() {
		a.log.Info("http.server.start", "event", "http.server.start", "addr", a.cfg.Server.Addr)
		errCh <- a.server.ListenAndServe()
	}()

	select {
	case <-ctx.Done():
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
		if err == http.ErrServerClosed {
			return nil
		}
		return err
	}
}
