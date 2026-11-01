package middleware

import (
	"context"
	"log/slog"
	"net/http"
	"net/http/httptest"
	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"testing"
	"time"
)

func TestRevokedSessionCannotExecuteHTTPCommands(t *testing.T) {
	ctx := context.Background()
	players := memory.NewPlayerRepo()
	sessions := memory.NewSessionStore()
	now := time.Now().UTC()
	if err := players.Create(ctx, player.Player{ID: "p", Name: "Player", Email: "p@example.invalid", Status: player.StatusActive}); err != nil {
		t.Fatal(err)
	}
	if err := sessions.Save(ctx, player.Session{ID: "sid", PlayerID: "p", ExpiresAt: now.Add(time.Hour)}); err != nil {
		t.Fatal(err)
	}
	tokens := jwtadapter.NewManager("test-secret", time.Hour, time.Hour)
	pair, err := tokens.Issue("p", "sid", now)
	if err != nil {
		t.Fatal(err)
	}
	calls := 0
	h := Auth(tokens, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { calls++; w.WriteHeader(204) }), service.NewPlayerService(players, sessions, slog.Default()))
	request := func() int {
		req := httptest.NewRequest("POST", "/", nil)
		req.Header.Set("Authorization", "Bearer "+pair.AccessToken)
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		return rec.Code
	}
	if status := request(); status != 204 {
		t.Fatal(status)
	}
	if err := sessions.RevokePlayer(ctx, "p"); err != nil {
		t.Fatal(err)
	}
	if status := request(); status != 401 || calls != 1 {
		t.Fatal("revoked request executed", status, calls)
	}
}
