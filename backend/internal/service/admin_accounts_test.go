package service

import (
	"context"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
	"testing"
	"time"
)

func TestAccountAdministrationRevokesSessionsAndProtectsLastAdmin(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewPlayerRepo()
	sessions := memory.NewSessionStore()
	for _, p := range []player.Player{{ID: "admin", Name: "Admin", Email: "admin@example.invalid", Role: player.RoleAdmin, Status: player.StatusActive}, {ID: "user", Name: "User", Email: "user@example.invalid", Role: player.RoleUser, Status: player.StatusActive}} {
		if err := repo.Create(ctx, p); err != nil {
			t.Fatal(err)
		}
	}
	if err := sessions.Save(ctx, player.Session{ID: "user-session", PlayerID: "user", ExpiresAt: time.Now().Add(time.Hour)}); err != nil {
		t.Fatal(err)
	}
	ps := NewPlayerService(repo, sessions, slog.Default())
	s := NewAdminService(ps, nil)
	if err := ps.ValidateAccess(ctx, "user", "user-session"); err != nil {
		t.Fatal(err)
	}
	if err := s.ChangeAccount(ctx, "user", "admin", player.StatusSuspended, player.RoleUser, "Злоупотребление"); err == nil {
		t.Fatal("ordinary player changed administrator")
	}
	if err := s.ChangeAccount(ctx, "admin", "admin", player.StatusSuspended, player.RoleUser, "Самоблокировка"); err == nil {
		t.Fatal("last admin disabled")
	}
	if err := ps.DeleteMe(ctx, "admin"); err == nil {
		t.Fatal("last admin deleted")
	}
	if err := s.ChangeAccount(ctx, "admin", "user", player.StatusSuspended, player.RoleUser, "Нарушение правил"); err != nil {
		t.Fatal(err)
	}
	if err := ps.ValidateAccess(ctx, "user", "user-session"); err == nil {
		t.Fatal("suspended account retained access")
	}
	if err := s.ChangeAccount(ctx, "admin", "user", player.StatusActive, player.RoleAdmin, "Назначение администратора"); err != nil {
		t.Fatal(err)
	}
	if err := ps.ValidateAccess(ctx, "user", "user-session"); err == nil {
		t.Fatal("unblock revived revoked session")
	}
	if err := s.ChangeAccount(ctx, "admin", "admin", player.StatusActive, player.RoleUser, "Передача полномочий"); err != nil {
		t.Fatal(err)
	}
	audit, err := s.AccountAudit(ctx, "user", 100)
	if err != nil || len(audit) != 3 {
		t.Fatal(audit, err)
	}
	if audit[2].PreviousStatus != player.StatusActive || audit[2].Status != player.StatusSuspended {
		t.Fatal("audit missing previous state", audit)
	}
}
