package httpadapter

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"strings"
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
	rec = httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/ready", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("readiness without database = %d", rec.Code)
	}
}

func TestRouterRejectsForeignOrigin(t *testing.T) {
	router := testRouterWithOrigins([]string{"https://city.example"})
	for _, method := range []string{http.MethodOptions, http.MethodPost} {
		req := httptest.NewRequest(method, "/api/v1/auth/login", nil)
		req.Header.Set("Origin", "https://foreign.example")
		rec := httptest.NewRecorder()
		router.ServeHTTP(rec, req)
		if rec.Code != http.StatusForbidden || rec.Header().Get("Access-Control-Allow-Origin") != "" {
			t.Fatalf("foreign origin %s: status=%d allow=%q", method, rec.Code, rec.Header().Get("Access-Control-Allow-Origin"))
		}
	}
	req := httptest.NewRequest(http.MethodOptions, "/api/v1/auth/login", nil)
	req.Header.Set("Origin", "https://city.example")
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)
	if rec.Code != http.StatusNoContent || rec.Header().Get("Access-Control-Allow-Origin") != "https://city.example" {
		t.Fatalf("allowed origin: status=%d allow=%q", rec.Code, rec.Header().Get("Access-Control-Allow-Origin"))
	}
}

func TestOpenAPIFreshness(t *testing.T) {
	router := testRouter()
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/swagger/openapi.json", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("swagger status = %d", rec.Code)
	}
	var runtimeSpec map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &runtimeSpec); err != nil {
		t.Fatalf("decode runtime openapi: %v", err)
	}
	fileSpec := readOpenAPIFile(t)
	if !reflect.DeepEqual(fileSpec, runtimeSpec) {
		t.Fatal("generated OpenAPI file differs from the runtime contract; run go run ./cmd/openapi-gen from backend/")
	}
	paths := runtimeSpec["paths"].(map[string]any)
	for path, raw := range paths {
		operations := raw.(map[string]any)
		for method := range operations {
			if strings.Contains(path, "{id}") {
				operation := operations[method].(map[string]any)
				parameters, ok := operation["parameters"].([]any)
				if !ok || len(parameters) == 0 {
					t.Errorf("OpenAPI operation %s %s is missing the id path parameter", strings.ToUpper(method), path)
				}
			}
			requestPath := strings.ReplaceAll(path, "{id}", "contract-id")
			if !strings.HasPrefix(path, "/health") && path != "/ready" && path != "/metrics" && path != "/swagger/openapi.json" {
				requestPath = "/api/v1" + requestPath
			}
			req := httptest.NewRequest(strings.ToUpper(method), requestPath, nil)
			rec := httptest.NewRecorder()
			router.ServeHTTP(rec, req)
			if rec.Code == http.StatusNotFound && strings.HasPrefix(rec.Header().Get("Content-Type"), "text/plain") {
				t.Errorf("OpenAPI operation %s %s is not mounted in the router", strings.ToUpper(method), path)
			}
			if rec.Code == http.StatusMethodNotAllowed {
				t.Errorf("OpenAPI operation %s %s is mounted with another method", strings.ToUpper(method), path)
			}
		}
	}
}

type openAPIFile = map[string]any

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
	return testRouterWithOrigins([]string{"*"})
}

func testRouterWithOrigins(origins []string) http.Handler {
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
		AllowedOrigins: origins,
		Auth:           service.NewAuthService(players, sessions, tokens, slog.Default()),
		Players:        service.NewPlayerService(players, sessions, slog.Default()),
		Worlds:         service.NewWorldService(worldRepo, slog.Default()),
		Forests:        service.NewForestService(worldRepo, economyService, slog.Default()),
		Buildings:      service.NewBuildingService(buildingRepo, worldRepo, slog.Default()),
		Economy:        economyService,
		Resources:      service.NewResourceService(economyRepo, economyService, slog.Default()),
		Production:     service.NewProductionService(economyRepo, economyService, slog.Default()),
		Fields:         service.NewFieldService(economyService, buildingRepo),
		Population:     service.NewPopulationService(economyService),
		Monsters:       service.NewMonsterService(monsterRepo, slog.Default()),
		Combat:         service.NewCombatService(service.NewMonsterService(monsterRepo, slog.Default()), slog.Default()),
		Threats:        service.NewThreatService(monsterRepo),
		Alliances:      service.NewAllianceService(socialRepo, economyService, slog.Default()),
		Chat:           service.NewChatService(socialRepo, socialRepo, slog.Default()),
		Market:         service.NewMarketService(socialRepo, economyService, slog.Default()),
		Tokens:         tokens,
	})
}
