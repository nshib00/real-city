package postgres

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"sync"
	"testing"
	"time"
)

func TestPersistentPvPBudgetAndAtomicAccountRevocation(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN to a migrated test database")
	}
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	ctx := context.Background()
	repo := NewPlayerRepo(db)
	sessions := NewSessionRepo(db)
	now := time.Now().UTC()
	prefix := fmt.Sprintf("pvp_admin_%d", now.UnixNano())
	admin, target := player.ID(prefix+"_admin"), player.ID(prefix+"_target")
	for _, p := range []player.Player{{ID: admin, Name: prefix + "admin", Email: prefix + "admin@example.invalid", Role: player.RoleAdmin, Status: player.StatusActive, CreatedAt: now, UpdatedAt: now, Profile: player.DefaultProfile("Admin", now)}, {ID: target, Name: prefix + "target", Email: prefix + "target@example.invalid", Role: player.RoleUser, Status: player.StatusActive, CreatedAt: now, UpdatedAt: now, Profile: player.DefaultProfile("Target", now)}} {
		if err := repo.Create(ctx, p); err != nil {
			t.Fatal(err)
		}
	}
	defer func() {
		for _, query := range []string{`DELETE FROM account_admin_audit WHERE actor_id=$1 OR player_id=$2`, `DELETE FROM player_sessions WHERE player_id IN ($1,$2)`, `DELETE FROM player_pvp_losses WHERE player_id IN ($1,$2)`, `DELETE FROM player_profiles WHERE player_id IN ($1,$2)`, `DELETE FROM players WHERE id IN ($1,$2)`} {
			if _, err := db.ExecContext(ctx, query, admin, target); err != nil {
				t.Error("cleanup", err)
			}
		}
	}()
	uow := NewUnitOfWork(db)
	err = uow.Do(ctx, func(ctx context.Context) error {
		if _, _, err := repo.PvPProtection(ctx, target, now, 100, 100); err != nil {
			return err
		}
		return errors.New("rollback hit")
	})
	if err == nil {
		t.Fatal("expected rollback")
	}
	state, _, err := repo.PvPProtection(ctx, target, now, 0, 0)
	if err != nil || state.Damage != 0 || state.Destructions != 0 {
		t.Fatal("loss counter escaped rollback", state, err)
	}
	var wg sync.WaitGroup
	hits := make(chan int, 20)
	failures := make(chan error, 20)
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, damage, err := NewPlayerRepo(db).PvPProtection(ctx, target, now, 100, 100)
			hits <- damage
			failures <- err
		}()
	}
	wg.Wait()
	close(hits)
	close(failures)
	for err := range failures {
		if err != nil {
			t.Fatal(err)
		}
	}
	total := 0
	for n := range hits {
		total += n
	}
	if total != 300 {
		t.Fatal("concurrent attackers exceeded destruction budget", total)
	}
	state, _, err = NewPlayerRepo(db).PvPProtection(ctx, target, now, 0, 0)
	if err != nil || state.Destructions != 3 {
		t.Fatal("state was not persisted", state, err)
	}
	sid := player.SessionID(prefix + "_session")
	if err := sessions.Save(ctx, player.Session{ID: sid, PlayerID: target, RefreshTokenHash: prefix, ExpiresAt: now.Add(time.Hour), CreatedAt: now, UpdatedAt: now}); err != nil {
		t.Fatal(err)
	}
	ps := service.NewPlayerService(repo, sessions, slog.Default())
	chat := service.NewChatService(NewSocialRepo(db), nil, slog.Default())
	chat.SetUnitOfWork(uow)
	adminService := service.NewAdminService(ps, chat)
	if err := adminService.ChangeAccount(ctx, admin, target, player.StatusSuspended, player.RoleUser, "Интеграционная проверка"); err != nil {
		t.Fatal(err)
	}
	if active, err := sessions.SessionActive(ctx, target, sid, now); err != nil || active {
		t.Fatal("session survived suspension", active, err)
	}
	audit, err := repo.AccountAudit(ctx, 100)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, a := range audit {
		if a.PlayerID == target {
			found = true
			if a.PreviousStatus != player.StatusActive || a.Status != player.StatusSuspended {
				t.Fatal(a)
			}
		}
	}
	if !found {
		t.Fatal("account change was not audited")
	}
}
