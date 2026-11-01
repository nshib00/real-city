package ws

import (
	"bufio"
	"context"
	"log/slog"
	"net"
	"net/http/httptest"
	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"testing"
	"time"
)

func TestOpenWebsocketClosesAfterSessionRevocation(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewPlayerRepo()
	sessions := memory.NewSessionStore()
	now := time.Now().UTC()
	if err := repo.Create(ctx, player.Player{ID: "p", Name: "Player", Email: "p@example.invalid", Status: player.StatusActive}); err != nil {
		t.Fatal(err)
	}
	if err := sessions.Save(ctx, player.Session{ID: "sid", PlayerID: "p", ExpiresAt: now.Add(time.Hour)}); err != nil {
		t.Fatal(err)
	}
	tokens := jwtadapter.NewManager("test", time.Hour, time.Hour)
	pair, err := tokens.Issue("p", "sid", now)
	if err != nil {
		t.Fatal(err)
	}
	g := NewGateway(tokens, service.NewEventBus(8), slog.Default())
	defer g.Shutdown()
	g.SetAccessValidator(service.NewPlayerService(repo, sessions, slog.Default()))
	req := httptest.NewRequest("GET", "/realtime?token="+pair.AccessToken, nil)
	if _, err := g.authenticate(req); err != nil {
		t.Fatal(err)
	}
	server, peer := net.Pipe()
	defer peer.Close()
	client := NewConnection(server, bufio.NewReader(server), "p", 8)
	defer client.Close("test")
	go g.watchAccess(req, client)
	if err := sessions.RevokePlayer(ctx, "p"); err != nil {
		t.Fatal(err)
	}
	select {
	case <-client.closed:
	case <-time.After(3 * time.Second):
		t.Fatal("revoked socket stayed open")
	}
	if _, err := g.authenticate(req); err == nil {
		t.Fatal("revoked token upgraded")
	}
}
