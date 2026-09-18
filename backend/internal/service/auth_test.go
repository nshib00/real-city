package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/adapter/memory"
)

func TestAuthServiceRegisterLoginRefreshLogout(t *testing.T) {
	repo := memory.NewPlayerRepo()
	sessions := memory.NewSessionStore()
	tokens := jwtadapter.NewManager("test-secret", time.Minute, time.Hour)
	auth := NewAuthService(repo, sessions, tokens, slog.Default())

	registered, err := auth.Register(context.Background(), RegisterInput{
		Email:    "Test@Example.com",
		Name:     "Frontier One",
		Password: "frontier123",
	})
	if err != nil {
		t.Fatalf("Register() error = %v", err)
	}
	if registered.Player.Email != "test@example.com" {
		t.Fatalf("registered email = %q", registered.Player.Email)
	}
	if registered.Player.Role != "user" {
		t.Fatalf("registered role = %q", registered.Player.Role)
	}
	if registered.Player.Profile.CityName != "Frontier One" || registered.Player.Profile.Level != 1 || registered.Player.Profile.XP != 0 {
		t.Fatalf("unexpected default profile: %#v", registered.Player.Profile)
	}

	loggedIn, err := auth.Login(context.Background(), LoginInput{
		Email:    "test@example.com",
		Password: "frontier123",
	})
	if err != nil {
		t.Fatalf("Login() error = %v", err)
	}
	if loggedIn.AccessToken == "" || loggedIn.RefreshToken == "" {
		t.Fatal("Login() returned empty tokens")
	}

	refreshed, err := auth.Refresh(context.Background(), loggedIn.RefreshToken, "", "")
	if err != nil {
		t.Fatalf("Refresh() error = %v", err)
	}
	if refreshed.RefreshToken == loggedIn.RefreshToken {
		t.Fatal("Refresh() did not rotate refresh token")
	}

	if err := auth.Logout(context.Background(), refreshed.RefreshToken); err != nil {
		t.Fatalf("Logout() error = %v", err)
	}
	if _, err := auth.Refresh(context.Background(), refreshed.RefreshToken, "", ""); err == nil {
		t.Fatal("Refresh() expected error after logout")
	}
}
