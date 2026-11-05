package handler

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
)

func TestTowerAlertHistoryUsesAuthenticatedPlayer(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewTowerAlertRepo()
	generation, _ := repo.BeginScan(ctx, "map")
	_, err := repo.Reconcile(ctx, "map", generation, time.Date(2026, 11, 5, 12, 0, 0, 0, time.UTC), []toweralert.Observation{{OwnerID: "owner", TowerID: "tower", MonsterID: "monster"}})
	if err != nil {
		t.Fatal(err)
	}
	h := NewTowerAlertHandler(repo)
	request := func(actor player.ID, path string) *httptest.ResponseRecorder {
		t.Helper()
		req := httptest.NewRequest(http.MethodGet, path, nil)
		req = req.WithContext(middleware.WithPlayerID(req.Context(), actor))
		response := httptest.NewRecorder()
		h.List(response, req)
		return response
	}
	owner := request("owner", "/tower-alerts")
	other := request("other", "/tower-alerts?player_id=owner")
	if owner.Code != http.StatusOK || !strings.Contains(owner.Body.String(), `"monster_id":"monster"`) {
		t.Fatalf("owner history: %d %s", owner.Code, owner.Body.String())
	}
	if other.Code != http.StatusOK || strings.Contains(other.Body.String(), `"monster_id":"monster"`) {
		t.Fatalf("other player's history leaked: %d %s", other.Code, other.Body.String())
	}
}
