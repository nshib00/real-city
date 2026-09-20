package httpadapter

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/service"
)

func TestRouterMiddlewareSmoke(t *testing.T) {
	router := testRouter()
	req := httptest.NewRequest(http.MethodOptions, "/api/v1/chat/messages", nil)
	req.Header.Set("Origin", "http://localhost:5173")
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)
	if rec.Code != http.StatusNoContent {
		t.Fatalf("preflight status = %d", rec.Code)
	}
	if rec.Header().Get("Access-Control-Allow-Headers") == "" {
		t.Fatalf("missing CORS allow headers")
	}

	req = httptest.NewRequest(http.MethodGet, "/health", nil)
	req.Header.Set("X-Request-ID", "smoke-request")
	rec = httptest.NewRecorder()
	router.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("health status = %d", rec.Code)
	}
	if rec.Header().Get("X-Request-ID") != "smoke-request" {
		t.Fatalf("missing request id header")
	}
}

func TestOpenAPIFreshness(t *testing.T) {
	router := testRouter()
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/swagger/openapi.json", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("swagger status = %d", rec.Code)
	}
	var runtimeSpec struct {
		Paths map[string]any `json:"paths"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &runtimeSpec); err != nil {
		t.Fatalf("decode runtime openapi: %v", err)
	}
	fileSpec := readOpenAPIFile(t)
	for path := range fileSpec.Paths {
		if _, ok := runtimeSpec.Paths[path]; !ok {
			t.Fatalf("runtime openapi is missing documented path %s", path)
		}
	}
}

type openAPIFile struct {
	Paths map[string]any `json:"paths"`
}

func readOpenAPIFile(t *testing.T) openAPIFile {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join("..", "..", "..", "docs", "swagger", "openapi.json"))
	if err != nil {
		t.Fatalf("read openapi file: %v", err)
	}
	var spec openAPIFile
	if err := json.Unmarshal(raw, &spec); err != nil {
		t.Fatalf("decode openapi file: %v", err)
	}
	return spec
}

func testRouter() http.Handler {
	players := memory.NewPlayerRepo()
	sessions := memory.NewSessionStore()
	tokens := jwtadapter.NewManager("route-contract-secret", 0, 0)
	worldRepo := memory.NewWorldRepo()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	monsterRepo := memory.NewMonsterRepo()
	socialRepo := memory.NewSocialRepo()
	economyService := service.NewEconomyService(economyRepo, buildingRepo, slog.Default())
	return NewRouter(slog.Default(), RouterDeps{
		Auth:       service.NewAuthService(players, sessions, tokens, slog.Default()),
		Players:    service.NewPlayerService(players, sessions, slog.Default()),
		Worlds:     service.NewWorldService(worldRepo, slog.Default()),
		Forests:    service.NewForestService(worldRepo, economyService, slog.Default()),
		Buildings:  service.NewBuildingService(buildingRepo, worldRepo, slog.Default()),
		Economy:    economyService,
		Resources:  service.NewResourceService(economyRepo, economyService, slog.Default()),
		Production: service.NewProductionService(economyRepo, economyService, slog.Default()),
		Fields:     service.NewFieldService(economyService, buildingRepo),
		Population: service.NewPopulationService(economyService),
		Monsters:   service.NewMonsterService(monsterRepo, slog.Default()),
		Combat:     service.NewCombatService(service.NewMonsterService(monsterRepo, slog.Default()), slog.Default()),
		Threats:    service.NewThreatService(monsterRepo),
		Alliances:  service.NewAllianceService(socialRepo, economyService, slog.Default()),
		Chat:       service.NewChatService(socialRepo, socialRepo, slog.Default()),
		Market:     service.NewMarketService(socialRepo, economyService, slog.Default()),
		Tokens:     tokens,
	})
}
