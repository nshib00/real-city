package httpadapter

import (
	"encoding/json"
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
	Monsters   *service.MonsterService
	Combat     *service.CombatService
	Threats    *service.ThreatService
	Alliances  *service.AllianceService
	Chat       *service.ChatService
	Market     *service.MarketService
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
	monsterHandler := handler.NewMonsterHandler(deps.Monsters, deps.Combat, deps.Threats)
	allianceHandler := handler.NewAllianceHandler(deps.Alliances)
	chatHandler := handler.NewChatHandler(deps.Chat)
	marketHandler := handler.NewMarketHandler(deps.Market)

	health := func(w http.ResponseWriter, r *http.Request) {
		JSON(w, http.StatusOK, Envelope{
			"status": "ok",
			"time":   time.Now().UTC().Format(time.RFC3339),
		})
	}
	mux.HandleFunc("GET /health", health)
	mux.HandleFunc("GET /healthz", health)
	mux.HandleFunc("GET /metrics", metrics)
	mux.HandleFunc("GET /swagger/openapi.json", swaggerOpenAPI)
	mux.HandleFunc("GET /api/v1/world", worldHandler.World)
	mux.HandleFunc("GET /api/v1/world/chunks", worldHandler.Chunks)
	mux.HandleFunc("GET /api/v1/world/viewport", worldHandler.Viewport)
	mux.HandleFunc("GET /api/v1/buildings/catalog", buildingHandler.Catalog)
	mux.HandleFunc("GET /api/v1/resources/nodes", economyHandler.ResourceNodes)
	mux.HandleFunc("GET /api/v1/production/recipes", economyHandler.ProductionRecipes)
	mux.HandleFunc("GET /api/v1/monsters/catalog", monsterHandler.Catalog)
	mux.HandleFunc("GET /api/v1/monsters", monsterHandler.List)
	mux.HandleFunc("GET /api/v1/threats", monsterHandler.Threats)
	mux.HandleFunc("GET /api/v1/raids", func(w http.ResponseWriter, r *http.Request) {
		JSON(w, http.StatusOK, Envelope{"raids": []any{}, "status": "placeholder"})
	})
	mux.HandleFunc("GET /api/v1/admin/status", func(w http.ResponseWriter, r *http.Request) {
		JSON(w, http.StatusOK, Envelope{"status": "placeholder"})
	})
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
	mux.Handle("POST /api/v1/fields/windleaf/advance", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.AdvanceField)))
	mux.Handle("POST /api/v1/fields/windleaf/harvest", middleware.Auth(deps.Tokens, http.HandlerFunc(economyHandler.HarvestField)))
	mux.Handle("GET /api/v1/monsters/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(monsterHandler.Get)))
	mux.Handle("POST /api/v1/monsters/{id}/attack", middleware.Auth(deps.Tokens, http.HandlerFunc(monsterHandler.Attack)))
	mux.Handle("GET /api/v1/alliances/me", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.Profile)))
	mux.Handle("POST /api/v1/alliances", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.Create)))
	mux.Handle("POST /api/v1/alliances/invites", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.Invite)))
	mux.Handle("PATCH /api/v1/alliances/invites/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.RespondInvite)))
	mux.Handle("PATCH /api/v1/alliances/roles", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.SetRole)))
	mux.Handle("POST /api/v1/alliances/treasury/donations", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.Donate)))
	mux.Handle("POST /api/v1/alliances/buffs", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.UpgradeBuff)))
	mux.Handle("POST /api/v1/alliances/territory-aid", middleware.Auth(deps.Tokens, http.HandlerFunc(allianceHandler.AddTerritoryAid)))
	mux.Handle("GET /api/v1/chat/messages", middleware.Auth(deps.Tokens, http.HandlerFunc(chatHandler.List)))
	mux.Handle("POST /api/v1/chat/messages", middleware.Auth(deps.Tokens, http.HandlerFunc(chatHandler.Send)))
	mux.HandleFunc("GET /api/v1/market/orders", marketHandler.List)
	mux.Handle("POST /api/v1/market/orders", middleware.Auth(deps.Tokens, http.HandlerFunc(marketHandler.Create)))
	mux.Handle("DELETE /api/v1/market/orders/{id}", middleware.Auth(deps.Tokens, http.HandlerFunc(marketHandler.Cancel)))
	return middleware.Chain(
		mux,
		middleware.RequestID(),
		middleware.Logger(log),
		middleware.Recoverer(func(r *http.Request, recovered any, stack []byte) {
			log.Error("http.panic", "event", "http.panic", "request_id", middleware.RequestIDFromContext(r.Context()), "path", r.URL.Path, "panic", recovered, "stack", string(stack))
		}),
		middleware.CORS([]string{"*"}),
		middleware.BodyLimit(1<<20),
		middleware.Timeout(5*time.Second),
		middleware.RateLimit(nil, middleware.DefaultRateLimitRules()),
		middleware.Idempotency(nil, 24*time.Hour),
	)
}

func metrics(w http.ResponseWriter, r *http.Request) {
	_ = r
	w.Header().Set("Content-Type", "text/plain; version=0.0.4")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("real_city_http_ready 1\n"))
}

func swaggerOpenAPI(w http.ResponseWriter, r *http.Request) {
	_ = r
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(OpenAPISpec())
}
