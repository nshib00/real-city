package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
)

func TestPlayerServiceAwardXPLevelsProfile(t *testing.T) {
	repo := memory.NewPlayerRepo()
	now := time.Date(2026, 8, 30, 12, 0, 0, 0, time.UTC)
	p := player.Player{
		ID:           "player_1",
		Email:        "test@example.com",
		Name:         "Frontier One",
		PasswordHash: "hash",
		Status:       player.StatusActive,
		Role:         player.RoleUser,
		Profile:      player.DefaultProfile("Frontier One", now),
		CreatedAt:    now,
		UpdatedAt:    now,
	}
	if err := repo.Create(context.Background(), p); err != nil {
		t.Fatalf("Create() error = %v", err)
	}

	service := NewPlayerService(repo, memory.NewSessionStore(), slog.Default())
	updated, err := service.AwardXP(context.Background(), p.ID, 260, "test")
	if err != nil {
		t.Fatalf("AwardXP() error = %v", err)
	}

	if updated.Profile.XP != 260 {
		t.Fatalf("expected 260 xp, got %d", updated.Profile.XP)
	}
	if updated.Profile.Level != 3 {
		t.Fatalf("expected level 3, got %d", updated.Profile.Level)
	}
}
