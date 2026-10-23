package handler

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
)

func TestPublicPlayerOnlyReturnsDisplayIdentity(t *testing.T) {
	repo := memory.NewPlayerRepo()
	handler := NewPlayerHandler(service.NewPlayerService(repo, nil, slog.Default()))
	request := httptest.NewRequest(http.MethodGet, "/players/player-2", nil)
	request.SetPathValue("id", "player-2")
	if err := repo.Create(request.Context(), player.Player{
		ID: "player-2", Name: "registered-name", Email: "private@example.com",
		Profile: player.Profile{DisplayName: "Игрок Севера", Level: 7},
	}); err != nil {
		t.Fatal(err)
	}
	response := httptest.NewRecorder()
	handler.Public(response, request)
	if response.Code != http.StatusOK {
		t.Fatalf("status %d: %s", response.Code, response.Body.String())
	}
	var body map[string]any
	if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
	if body["display_name"] != "Игрок Севера" || body["level"] != float64(7) || body["email"] != nil {
		t.Fatalf("unexpected public player: %#v", body)
	}
}
