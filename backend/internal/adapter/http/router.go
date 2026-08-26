package httpadapter

import (
	"log/slog"
	"net/http"
	"time"

	"real-city/backend/internal/adapter/http/handler"
	"real-city/backend/internal/adapter/http/middleware"
	jwtadapter "real-city/backend/internal/adapter/jwt"
	wsadapter "real-city/backend/internal/adapter/ws"
	"real-city/backend/internal/service"
)

type RouterDeps struct {
	Auth       *service.AuthService
	Players    *service.PlayerService
	Worlds     *service.WorldService
	Forests    *service.ForestService
	Buildings  *service.BuildingService
	Economy    *service.EconomyService
	Resources  *service.ResourceService
	Production *service.ProductionService
	Fields     *service.FieldService
	Population *service.PopulationService
	Tokens     *jwtadapter.Manager
	Realtime   *wsadapter.Gateway
}

func NewRouter(log *slog.Logger, deps RouterDeps) http.Handler {
	mux := http.NewServeMux()
	authHandler := handler.NewAuthHandler(deps.Auth)
	playerHandler := handler.NewPlayerHandler(deps.Players)
	worldHandler := handler.NewWorldHandler(deps.Worlds, deps.Forests)
	buildingHandler := handler.NewBuildingHandler(deps.Buildings)
	economyHandler := handler.NewEconomyHandler(deps.Economy, deps.Resources, deps.Production, deps.Fields, deps.Population)

	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		JSON(w, http.StatusOK, Envelope{
			"status": "ok",
			"time":   time.Now().UTC().Format(time.RFC3339),
		})
	})
	mux.HandleFunc("GET /api/v1/world", worldHandler.World)
	mux.HandleFunc("GET /api/v1/world/chunks", worldHandler.Chunks)
	mux.HandleFunc("GET /api/v1/world/viewport", worldHandler.Viewport)
	mux.HandleFunc("GET /api/v1/buildings/catalog", buildingHandler.Catalog)
	mux.HandleFunc("GET /api/v1/resources/nodes", economyHandler.ResourceNodes)
	mux.HandleFunc("GET /api/v1/production/recipes", economyHandler.ProductionRecipes)
	if deps.Realtime != nil {
		mux.Handle("GET /api/v1/realtime", deps.Realtime)
	}
	mux.HandleFunc("POST /api/v1/auth/register", authHandler.Register)
	mux.HandleFunc("POST /api/v1/auth/login", authHandler.Login)
	mux.HandleFunc("POST /api/v1/auth/refresh", authHandler.Refresh)
	mux.Handle("POST /api/v1/auth/logout", middleware.Auth(deps.Tokens, http.HandlerFunc(authHandler.Logout)))
	mux.Handle("GET /api/v1/players/me", middleware.Auth(deps.Tokens, http.HandlerFunc(playerHandler.Me)))
	mux.Handle("PATCH /api/v1/players/me", middleware.Auth(deps.Tokens, http.HandlerFunc(playerHandler.UpdateMe)))
	mux.Handle("PATCH /api/v1/players/me/password", middleware.Auth(deps.Tokens, http.HandlerFunc(playerHandler.ChangePassword)))
	mux.Handle("DELETE /api/v1/players/me", middleware.Auth(deps.Tokens, http.HandlerFunc(playerHandler.DeleteMe)))
	mux.Handle("GET /api/v1/buildings", middleware.Auth(deps.Tokens, http.HandlerFunc(buildingHandler.List)))
	mux.Handle("POST /api/v1/world/tiles/chop-forest", middleware.Auth(deps.Tokens, http.HandlerFunc(worldHandler.ChopForest)))
	mux.Handle("POST /api/v1/buildings", middleware.Auth(deps.Tokens, http.HandlerFunc(buildingHandler.Place)))
	mux.Handle("GET /api/v1/buildings/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(buildingHandler.Get)))
	mux.Handle("PATCH /api/v1/buildings/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(buildingHandler.Patch)))
	mux.Handle("DELETE /api/v1/buildings/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(buildingHandler.Delete)))
	mux.Handle("GET /api/v1/economy/inventory", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.Inventory)))
	mux.Handle("GET /api/v1/economy/transactions", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.Transactions)))
	mux.Handle("GET /api/v1/economy/population", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.Population)))
	mux.Handle("PATCH /api/v1/resources/nodes/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.PatchResourceNode)))
	mux.Handle("GET /api/v1/production/jobs", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.ProductionJobs)))
	mux.Handle("POST /api/v1/production/jobs", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.StartProduction)))
	mux.Handle("PATCH /api/v1/production/jobs/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.PatchProduction)))
	mux.Handle("POST /api/v1/fields/windleaf/harvest", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.HarvestField)))
	return accessLog(log, mux)
}

func accessLog(log *slog.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		recorder := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(recorder, r)
		log.Info("http.request",
			"event", "http.request",
			"method", r.Method,
			"path", r.URL.Path,
			"status", recorder.status,
			"duration_ms", time.Since(start).Milliseconds(),
			"ip", r.RemoteAddr,
			"user_agent", r.UserAgent(),
		)
	})
}

type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(status int) {
	r.status = status
	r.ResponseWriter.WriteHeader(status)
}
