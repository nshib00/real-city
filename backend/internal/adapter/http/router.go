package httpadapter

import (
	"database/sql"
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
	AppEnv         string
	AllowedOrigins []string
	Auth           *service.AuthService
	Players        *service.PlayerService
	Worlds         *service.WorldService
	Forests        *service.ForestService
	Buildings      *service.BuildingService
	Economy        *service.EconomyService
	Resources      *service.ResourceService
	Production     *service.ProductionService
	Fields         *service.FieldService
	Population     *service.PopulationService
	Monsters       *service.MonsterService
	Combat         *service.CombatService
	Threats        *service.ThreatService
	Alliances      *service.AllianceService
	Chat           *service.ChatService
	Market         *service.MarketService
	TowerAlerts    service.TowerAlertRepository
	Tokens         *jwtadapter.Manager
	Realtime       *wsadapter.Gateway
	DBPool         *sql.DB
	Idempotency    middleware.IdempotencyStore
}

func NewRouter(log *slog.Logger, deps RouterDeps) http.Handler {
	mux := http.NewServeMux()
	var readiness *readinessProbe
	if deps.DBPool != nil {
		readiness = newReadinessProbe(deps.DBPool)
	}
	authenticated := func(tokens *jwtadapter.Manager, next http.Handler) http.Handler {
		return middleware.Auth(tokens, next, deps.Players)
	}
	authHandler := handler.NewAuthHandler(deps.Auth)
	playerHandler := handler.NewPlayerHandler(deps.Players)
	worldHandler := handler.NewWorldHandler(deps.Worlds, deps.Forests)
	buildingHandler := handler.NewBuildingHandler(deps.Buildings)
	economyHandler := handler.NewEconomyHandler(deps.Economy, deps.Resources, deps.Production, deps.Fields, deps.Population)
	monsterHandler := handler.NewMonsterHandler(deps.Monsters, deps.Combat, deps.Threats)
	combatHandler := handler.NewCombatHandler(deps.Combat)
	towerAlertHandler := handler.NewTowerAlertHandler(deps.TowerAlerts)
	allianceHandler := handler.NewAllianceHandler(deps.Alliances)
	chatHandler := handler.NewChatHandler(deps.Chat)
	marketHandler := handler.NewMarketHandler(deps.Market)
	adminHandler := handler.NewAdminHandler(service.NewAdminService(deps.Players, deps.Chat))
	mux.Handle("PATCH /api/v1/admin/players/{id}", authenticated(deps.Tokens, http.HandlerFunc(adminHandler.ChangeAccount)))
	mux.Handle("GET /api/v1/admin/accounts/audit", authenticated(deps.Tokens, http.HandlerFunc(adminHandler.AccountAudit)))
	httpMetrics := middleware.NewHTTPMetrics()
	idempotentAuth := func(next http.HandlerFunc) http.Handler {
		return authenticated(deps.Tokens, middleware.Idempotency(deps.Idempotency, 24*time.Hour)(next))
	}

	health := func(w http.ResponseWriter, r *http.Request) {
		JSON(w, http.StatusOK, Envelope{
			"status": "ok",
			"time":   time.Now().UTC().Format(time.RFC3339),
		})
	}
	mux.HandleFunc("GET /health", health)
	mux.HandleFunc("GET /healthz", health)
	mux.HandleFunc("GET /ready", func(w http.ResponseWriter, r *http.Request) {
		if readiness != nil && !readiness.ready(r.Context()) {
			JSON(w, http.StatusServiceUnavailable, Envelope{"status": "unavailable"})
			return
		}
		JSON(w, http.StatusOK, Envelope{"status": "ready"})
	})
	mux.HandleFunc("GET /metrics", metrics(httpMetrics, deps.Realtime, deps.DBPool))
	mux.HandleFunc("GET /swagger/openapi.json", swaggerOpenAPI)
	mux.HandleFunc("GET /api/v1/world", worldHandler.World)
	mux.HandleFunc("GET /api/v1/world/chunks", worldHandler.Chunks)
	mux.HandleFunc("GET /api/v1/world/viewport", worldHandler.Viewport)
	mux.HandleFunc("GET /api/v1/buildings/catalog", buildingHandler.Catalog)
	mux.HandleFunc("GET /api/v1/resources/nodes", economyHandler.ResourceNodes)
	mux.HandleFunc("GET /api/v1/production/recipes", economyHandler.ProductionRecipes)
	mux.HandleFunc("GET /api/v1/monsters/catalog", monsterHandler.Catalog)
	mux.HandleFunc("GET /api/v1/monsters", monsterHandler.List)
	mux.HandleFunc("GET /api/v1/monster-loot", monsterHandler.Loot)
	mux.HandleFunc("GET /api/v1/threats", monsterHandler.Threats)
	mux.HandleFunc("GET /api/v1/combat/rules", combatHandler.Rules)
	mux.HandleFunc("GET /api/v1/players/levels", playerHandler.Levels)
	mux.Handle("GET /api/v1/admin/status", authenticated(deps.Tokens, http.HandlerFunc(adminHandler.Status)))
	mux.Handle("GET /api/v1/admin/players", authenticated(deps.Tokens, http.HandlerFunc(adminHandler.Players)))
	mux.Handle("GET /api/v1/admin/chat/messages", authenticated(deps.Tokens, http.HandlerFunc(adminHandler.Flagged)))
	mux.Handle("PATCH /api/v1/admin/chat/messages/{id}", authenticated(deps.Tokens, http.HandlerFunc(adminHandler.Moderate)))
	mux.Handle("GET /api/v1/admin/audit", authenticated(deps.Tokens, http.HandlerFunc(adminHandler.Audit)))
	if deps.Realtime != nil {
		mux.Handle("GET /api/v1/realtime", deps.Realtime)
	}
	mux.HandleFunc("POST /api/v1/auth/register", authHandler.Register)
	mux.HandleFunc("POST /api/v1/auth/login", authHandler.Login)
	mux.HandleFunc("POST /api/v1/auth/refresh", authHandler.Refresh)
	mux.Handle("POST /api/v1/auth/logout", authenticated(deps.Tokens, http.HandlerFunc(authHandler.Logout)))
	mux.Handle("GET /api/v1/players/me", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.Me)))
	mux.Handle("POST /api/v1/players/me/presence", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.UpdatePresence)))
	mux.Handle("GET /api/v1/players/nearby", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.NearbyPresence)))
	mux.Handle("GET /api/v1/players/{id}/profile", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.PublicProfile)))
	mux.Handle("GET /api/v1/players/{id}", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.Public)))
	mux.Handle("PATCH /api/v1/players/me", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.UpdateMe)))
	mux.Handle("PATCH /api/v1/players/me/password", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.ChangePassword)))
	mux.Handle("DELETE /api/v1/players/me", authenticated(deps.Tokens, http.HandlerFunc(playerHandler.DeleteMe)))
	mux.Handle("GET /api/v1/buildings", authenticated(deps.Tokens, http.HandlerFunc(buildingHandler.List)))
	mux.Handle("POST /api/v1/world/tiles/chop-forest", authenticated(deps.Tokens, http.HandlerFunc(worldHandler.ChopForest)))
	mux.Handle("POST /api/v1/buildings", idempotentAuth(buildingHandler.Place))
	mux.Handle("POST /api/v1/buildings/{id}/weapons", idempotentAuth(combatHandler.BuildingWeapon))
	mux.Handle("POST /api/v1/combat/monsters", idempotentAuth(combatHandler.CreateMonster))
	mux.Handle("GET /api/v1/buildings/{id}/repair", authenticated(deps.Tokens, http.HandlerFunc(buildingHandler.RepairStatus)))
	mux.Handle("GET /api/v1/buildings/{id}", authenticated(deps.Tokens, http.HandlerFunc(buildingHandler.Get)))
	mux.Handle("PATCH /api/v1/buildings/{id}", authenticated(deps.Tokens, http.HandlerFunc(buildingHandler.Patch)))
	mux.Handle("DELETE /api/v1/buildings/{id}", authenticated(deps.Tokens, http.HandlerFunc(buildingHandler.Delete)))
	mux.Handle("GET /api/v1/economy/inventory", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.Inventory)))
	mux.Handle("GET /api/v1/economy/transactions", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.Transactions)))
	mux.Handle("GET /api/v1/economy/population", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.Population)))
	mux.Handle("PATCH /api/v1/resources/nodes/{id}", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.PatchResourceNode)))
	mux.Handle("GET /api/v1/production/jobs", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.ProductionJobs)))
	mux.Handle("POST /api/v1/production/jobs", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.StartProduction)))
	mux.Handle("PATCH /api/v1/production/jobs/{id}", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.PatchProduction)))
	mux.Handle("POST /api/v1/fields/advance", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.AdvanceField)))
	mux.Handle("POST /api/v1/fields/harvest", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.HarvestField)))
	mux.Handle("POST /api/v1/fields/windleaf/advance", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.AdvanceField)))
	mux.Handle("POST /api/v1/fields/windleaf/harvest", authenticated(deps.Tokens, http.HandlerFunc(economyHandler.HarvestField)))
	mux.Handle("GET /api/v1/monsters/{id}", authenticated(deps.Tokens, http.HandlerFunc(monsterHandler.Get)))
	mux.Handle("POST /api/v1/monsters/{id}/weapons", idempotentAuth(monsterHandler.UseWeapon))
	mux.Handle("GET /api/v1/combat/attacks", authenticated(deps.Tokens, http.HandlerFunc(monsterHandler.PendingWeapons)))
	mux.Handle("GET /api/v1/combat/history", authenticated(deps.Tokens, http.HandlerFunc(combatHandler.History)))
	mux.Handle("GET /api/v1/tower-alerts", authenticated(deps.Tokens, http.HandlerFunc(towerAlertHandler.List)))
	mux.Handle("PUT /api/v1/buildings/{id}/tower-share", authenticated(deps.Tokens, http.HandlerFunc(towerAlertHandler.PutShare)))
	mux.Handle("DELETE /api/v1/buildings/{id}/tower-share", authenticated(deps.Tokens, http.HandlerFunc(towerAlertHandler.DeleteShare)))
	mux.Handle("POST /api/v1/monster-loot/{id}/claim", authenticated(deps.Tokens, http.HandlerFunc(monsterHandler.ClaimLoot)))
	mux.Handle("POST /api/v1/alliances/members/{id}/leadership", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.TransferLeadership)))
	mux.Handle("DELETE /api/v1/alliances/me", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.Leave)))
	mux.Handle("DELETE /api/v1/alliances/members/{id}", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.Kick)))
	mux.Handle("GET /api/v1/alliances/me", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.Profile)))
	mux.Handle("POST /api/v1/alliances", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.Create)))
	mux.Handle("POST /api/v1/alliances/invites", idempotentAuth(allianceHandler.Invite))
	mux.Handle("PATCH /api/v1/alliances/invites/{id}", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.RespondInvite)))
	mux.Handle("PATCH /api/v1/alliances/roles", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.SetRole)))
	mux.Handle("POST /api/v1/alliances/treasury/donations", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.Donate)))
	mux.Handle("POST /api/v1/alliances/treasury/spend", idempotentAuth(allianceHandler.SpendTreasury))
	mux.Handle("POST /api/v1/alliances/buffs", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.UpgradeBuff)))
	mux.Handle("POST /api/v1/alliances/territory-aid", authenticated(deps.Tokens, http.HandlerFunc(allianceHandler.AddTerritoryAid)))
	mux.Handle("PATCH /api/v1/chat/read", authenticated(deps.Tokens, http.HandlerFunc(chatHandler.MarkRead)))
	mux.Handle("GET /api/v1/chat/messages", authenticated(deps.Tokens, http.HandlerFunc(chatHandler.List)))
	mux.Handle("POST /api/v1/chat/messages", authenticated(deps.Tokens, http.HandlerFunc(chatHandler.Send)))
	mux.HandleFunc("GET /api/v1/market/orders", marketHandler.List)
	mux.Handle("POST /api/v1/market/orders", idempotentAuth(marketHandler.Create))
	mux.Handle("DELETE /api/v1/market/orders/{id}", authenticated(deps.Tokens, http.HandlerFunc(marketHandler.Cancel)))
	return middleware.Chain(
		mux,
		middleware.RequestID(),
		middleware.Logger(log),
		middleware.Metrics(httpMetrics, mux),
		middleware.Recoverer(func(r *http.Request, recovered any, stack []byte) {
			logRecoveredPanic(log, deps.AppEnv, r, recovered, stack)
		}),
		middleware.CORS(deps.AllowedOrigins),
		middleware.BodyLimit(1<<20),
		middleware.Timeout(15*time.Second),
		middleware.RateLimit(nil, middleware.DefaultRateLimitRules()),
	)
}

func logRecoveredPanic(log *slog.Logger, appEnv string, r *http.Request, recovered any, stack []byte) {
	attributes := []any{"event", "http.panic", "request_id", middleware.RequestIDFromContext(r.Context())}
	if appEnv != "production" {
		attributes = append(attributes, "path", r.URL.Path, "panic", recovered, "stack", string(stack))
	}
	log.Error("http.panic", attributes...)
}

func swaggerOpenAPI(w http.ResponseWriter, r *http.Request) {
	_ = r
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(OpenAPISpec())
}
