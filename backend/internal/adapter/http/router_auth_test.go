package httpadapter

import (
	"bytes"
	"encoding/json"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/service"
)

func TestAuthAndPlayerRoutes(t *testing.T) {
	players := memory.NewPlayerRepo()
	sessions := memory.NewSessionStore()
	tokens := jwtadapter.NewManager("route-test-secret", time.Minute, time.Hour)
	router := NewRouter(slog.Default(), RouterDeps{
		Auth:      service.NewAuthService(players, sessions, tokens, slog.Default()),
		Players:   service.NewPlayerService(players, sessions, slog.Default()),
		Worlds:    service.NewWorldService(memory.NewWorldRepo(), slog.Default()),
		Buildings: service.NewBuildingService(memory.NewBuildingRepo(), memory.NewWorldRepo(), slog.Default()),
		Tokens:    tokens,
	})

	registerBody := `{"email":"route@example.com","name":"Route City","password":"frontier123"}`
	registerResponse := doJSON(t, router, http.MethodPost, "/api/v1/auth/register", "", registerBody)
	if registerResponse.Code != http.StatusCreated {
		t.Fatalf("register status = %d body = %s", registerResponse.Code, registerResponse.Body.String())
	}
	var auth struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
		Player       struct {
			Role string `json:"role"`
		} `json:"player"`
	}
	if err := json.Unmarshal(registerResponse.Body.Bytes(), &auth); err != nil {
		t.Fatalf("decode auth response: %v", err)
	}
	if auth.AccessToken == "" || auth.RefreshToken == "" {
		t.Fatal("register returned empty tokens")
	}
	if auth.Player.Role != "user" {
		t.Fatalf("register role = %q", auth.Player.Role)
	}

	meResponse := doJSON(t, router, http.MethodGet, "/api/v1/players/me", auth.AccessToken, "")
	if meResponse.Code != http.StatusOK {
		t.Fatalf("me status = %d body = %s", meResponse.Code, meResponse.Body.String())
	}

	changePasswordResponse := doJSON(t, router, http.MethodPatch, "/api/v1/players/me/password", auth.AccessToken, `{"current_password":"frontier123","new_password":"frontier456"}`)
	if changePasswordResponse.Code != http.StatusOK {
		t.Fatalf("change password status = %d body = %s", changePasswordResponse.Code, changePasswordResponse.Body.String())
	}

	loginResponse := doJSON(t, router, http.MethodPost, "/api/v1/auth/login", "", `{"email":"route@example.com","password":"frontier456"}`)
	if loginResponse.Code != http.StatusOK {
		t.Fatalf("login status = %d body = %s", loginResponse.Code, loginResponse.Body.String())
	}
}

func doJSON(t *testing.T, router http.Handler, method string, path string, token string, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, path, bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)
	return rec
}
