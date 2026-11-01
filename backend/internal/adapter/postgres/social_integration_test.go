package postgres

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"sync"
	"testing"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
)

type rejectInsertedOrder struct{ *SocialRepo }

func (r rejectInsertedOrder) CreateOrder(ctx context.Context, a market.Order) error {
	if err := r.SocialRepo.CreateOrder(ctx, a); err != nil {
		return err
	}
	return errors.New("injected failure after SQL insert")
}
func TestSocialPersistenceAndMarketAtomicity(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN to a migrated test database")
	}
	ctx := context.Background()
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	id := player.ID(fmt.Sprintf("social_test_%d", time.Now().UnixNano()))
	if _, err = db.ExecContext(ctx, `INSERT INTO players(id,email,name,password_hash) VALUES($1,$2,$1,'test')`, id, string(id)+"@example.invalid"); err != nil {
		t.Fatal(err)
	}
	defer db.ExecContext(ctx, `DELETE FROM players WHERE id=$1`, id)
	repo := NewSocialRepo(db)
	ecoRepo := NewEconomyRepo(db)
	eco := service.NewEconomyService(ecoRepo, nil, slog.Default())
	uow := NewUnitOfWork(db)
	eco.SetUnitOfWork(uow)
	inv, err := eco.Inventory(ctx, id)
	if err != nil {
		t.Fatal(err)
	}
	inv.Items[economy.ResourceWood] = 100
	inv.Items[economy.ResourceCoins] = 1000
	if err = ecoRepo.SaveInventory(ctx, inv); err != nil {
		t.Fatal(err)
	}
	failed := service.NewMarketService(rejectInsertedOrder{repo}, eco, slog.Default())
	failed.SetUnitOfWork(uow)
	if _, err = failed.Create(ctx, id, market.SideSell, economy.ResourceWood, 20, 100); err == nil {
		t.Fatal("expected rollback")
	}
	after, _ := eco.Inventory(ctx, id)
	if after.Items[economy.ResourceWood] != 100 || after.Items[economy.ResourceCoins] != 1000 {
		t.Fatal("reserve was not rolled back")
	}
	var count int
	if err = db.QueryRowContext(ctx, `SELECT count(*) FROM market_orders WHERE player_id=$1`, id).Scan(&count); err != nil || count != 0 {
		t.Fatal("order escaped rollback")
	}
	svc := service.NewMarketService(repo, eco, slog.Default())
	svc.SetUnitOfWork(uow)
	order, err := svc.Create(ctx, id, market.SideSell, economy.ResourceWood, 20, 100)
	if err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	out := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); _, e := svc.Cancel(ctx, id, order.ID); out <- e }()
	}
	wg.Wait()
	close(out)
	success := 0
	for e := range out {
		if e == nil {
			success++
		}
	}
	after, _ = eco.Inventory(ctx, id)
	if success != 1 || after.Items[economy.ResourceWood] != 100 || after.Items[economy.ResourceCoins] != 995 {
		t.Fatal("concurrent cancellation duplicated refund")
	}
	buyerID := player.ID(string(id) + "_buyer")
	if _, err = db.ExecContext(ctx, `INSERT INTO players(id,email,name,password_hash) VALUES($1,$2,$1,'test')`, buyerID, string(buyerID)+"@example.invalid"); err != nil {
		t.Fatal(err)
	}
	defer db.ExecContext(ctx, `DELETE FROM players WHERE id=$1`, buyerID)
	buyerInventory, err := eco.Inventory(ctx, buyerID)
	if err != nil {
		t.Fatal(err)
	}
	buyerInventory.Items[economy.ResourceCoins] = 1000
	buyerInventory.Items[economy.ResourceWood] = 0
	if err = ecoRepo.SaveInventory(ctx, buyerInventory); err != nil {
		t.Fatal(err)
	}
	if _, err = svc.Create(ctx, id, market.SideSell, economy.ResourceWood, 20, 100); err != nil {
		t.Fatal(err)
	}
	trade, err := svc.Create(ctx, buyerID, market.SideBuy, economy.ResourceWood, 10, 60)
	if err != nil || trade.Status != market.StatusFilled {
		t.Fatalf("partial SQL match: order=%+v error=%v", trade, err)
	}
	buyerInventory, err = eco.Inventory(ctx, buyerID)
	if err != nil || buyerInventory.Items[economy.ResourceWood] != 10 || buyerInventory.Items[economy.ResourceCoins] != 947 {
		t.Fatalf("partial SQL settlement: inventory=%+v error=%v", buyerInventory, err)
	}
	now := time.Now().UTC()
	a := alliance.Alliance{ID: alliance.ID(string(id)), Name: string(id), LeaderID: id, Level: 1, CreatedAt: now, UpdatedAt: now}
	if err = repo.Create(ctx, a); err != nil {
		t.Fatal(err)
	}
	if err = repo.SaveMembership(ctx, alliance.Membership{AllianceID: a.ID, PlayerID: id, Role: alliance.RoleLeader, JoinedAt: now}); err != nil {
		t.Fatal(err)
	}
	if err = repo.AddTreasuryEntry(ctx, alliance.TreasuryEntry{ID: alliance.LedgerID(string(id)), AllianceID: a.ID, PlayerID: id, Kind: alliance.LedgerDonation, Resource: economy.ResourceWood, Amount: 2, CreatedAt: now}); err != nil {
		t.Fatal(err)
	}
	if err = repo.SaveBuff(ctx, alliance.Buff{AllianceID: a.ID, ID: "build_speed", Level: 1, UpdatedAt: now}); err != nil {
		t.Fatal(err)
	}
	if err = repo.AddMessage(ctx, chat.Message{ID: chat.MessageID(string(id)), AuthorID: id, Channel: chat.ChannelAlliance, AllianceID: a.ID, Body: "persistent", CreatedAt: now}); err != nil {
		t.Fatal(err)
	}
	db2, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db2.Close()
	reloaded := NewSocialRepo(db2)
	if _, _, err = reloaded.FindByPlayer(ctx, id); err != nil {
		t.Fatal(err)
	}
	messages, err := reloaded.ListMessages(ctx, id, chat.ChannelAlliance, a.ID, 10)
	if err != nil || len(messages) != 1 {
		t.Fatal("chat lost on reconnect")
	}
	entries, err := reloaded.ListTreasury(ctx, a.ID, 10)
	if err != nil || len(entries) != 1 {
		t.Fatal("treasury lost")
	}
	buffs, err := reloaded.ListBuffs(ctx, a.ID)
	if err != nil || len(buffs) != 1 {
		t.Fatal("buff lost")
	}
}
