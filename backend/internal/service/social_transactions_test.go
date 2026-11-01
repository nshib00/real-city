package service

import (
	"context"
	"errors"
	"log/slog"
	"sync"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
)

type failingOrders struct {
	*memory.SocialRepo
	failCreate bool
	failUpdate bool
}

func (r *failingOrders) CreateOrder(ctx context.Context, a market.Order) error {
	if r.failCreate {
		return errors.New("injected create failure")
	}
	return r.SocialRepo.CreateOrder(ctx, a)
}
func (r *failingOrders) UpdateOrder(ctx context.Context, a market.Order) error {
	if r.failUpdate {
		return errors.New("injected update failure")
	}
	return r.SocialRepo.UpdateOrder(ctx, a)
}
func TestMarketRollbackAndConcurrentCancel(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := &failingOrders{SocialRepo: memory.NewSocialRepo(), failCreate: true}
	er := memory.NewEconomyRepo()
	eco := NewEconomyService(er, nil, slog.Default())
	marketService := NewMarketService(repo, eco, slog.Default())
	before := grantTestResources(t, ctx, eco, "p1", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 50}, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: 100})
	bus := NewEventBus(32)
	eco.SetEventBus(bus)
	events := bus.Subscribe(ctx)
	if _, err := marketService.Create(ctx, "p1", market.SideSell, economy.ResourceWood, 50, 100); err == nil {
		t.Fatal("expected injected failure")
	}
	after, _ := eco.Inventory(ctx, "p1")
	if after.Items[economy.ResourceWood] != before.Items[economy.ResourceWood] || after.Items[economy.ResourceCoins] != before.Items[economy.ResourceCoins] {
		t.Fatal("failed order spent resources")
	}
	select {
	case <-events:
		t.Fatal("rolled back event escaped")
	default:
	}
	repo.failCreate = false
	order, err := marketService.Create(ctx, "p1", market.SideSell, economy.ResourceWood, 50, 100)
	if err != nil {
		t.Fatal(err)
	}
	repo.failUpdate = true
	if _, err = marketService.Cancel(ctx, "p1", order.ID); err == nil {
		t.Fatal("expected update failure")
	}
	after, _ = eco.Inventory(ctx, "p1")
	if after.Items[economy.ResourceWood] != before.Items[economy.ResourceWood]-50 {
		t.Fatal("refund escaped rollback")
	}
	repo.failUpdate = false
	var wg sync.WaitGroup
	var mu sync.Mutex
	success := 0
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, e := marketService.Cancel(ctx, "p1", order.ID); e == nil {
				mu.Lock()
				success++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	after, _ = eco.Inventory(ctx, "p1")
	if success != 1 || after.Items[economy.ResourceWood] != before.Items[economy.ResourceWood] {
		t.Fatal("cancel refunded more than once")
	}
}
func TestAllianceRemovalPermissionsAndChatPrivacy(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewSocialRepo()
	eco := NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default())
	svc := NewAllianceService(repo, eco, slog.Default())
	profile, err := svc.Create(ctx, "leader", "Северный союз")
	if err != nil {
		t.Fatal(err)
	}
	if err = repo.SaveMembership(ctx, alliance.Membership{AllianceID: profile.Alliance.ID, PlayerID: "member", Role: alliance.RoleMember, JoinedAt: time.Now()}); err != nil {
		t.Fatal(err)
	}
	if err = svc.Leave(ctx, "leader"); err == nil {
		t.Fatal("leader orphaned members")
	}
	if err = svc.Kick(ctx, "member", "leader"); err == nil {
		t.Fatal("member kicked leader")
	}
	if err = svc.TransferLeadership(ctx, "leader", "member"); err != nil {
		t.Fatal(err)
	}
	if err = svc.Leave(ctx, "leader"); err != nil {
		t.Fatal(err)
	}
	chatSvc := NewChatService(repo, repo, slog.Default())
	bus := NewEventBus(8)
	chatSvc.SetEventBus(bus)
	stream := bus.Subscribe(ctx)
	if _, err = chatSvc.Send(ctx, "member", chat.ChannelAlliance, "", "Секрет союза"); err != nil {
		t.Fatal(err)
	}
	event := <-stream
	if event.PlayerID != "member" {
		t.Fatal("alliance message sent to former member")
	}
	select {
	case <-stream:
		t.Fatal("unexpected recipient")
	default:
	}
	if _, err = chatSvc.List(ctx, "leader", chat.ChannelAlliance, 10); err == nil {
		t.Fatal("former member reads alliance")
	}
	if err = svc.Leave(ctx, "member"); err != nil {
		t.Fatal(err)
	}
	if _, err = repo.FindByID(ctx, profile.Alliance.ID); err == nil {
		t.Fatal("empty alliance not dissolved")
	}
}
func TestChatReadCursorMonotonicAndScoped(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewSocialRepo()
	svc := NewChatService(repo, repo, slog.Default())
	msg, err := svc.Send(ctx, "author", chat.ChannelGlobal, "", "Новое сообщение")
	if err != nil {
		t.Fatal(err)
	}
	state, err := svc.ReadState(ctx, "reader", chat.ChannelGlobal)
	if err != nil || state.Unread != 1 {
		t.Fatalf("unread: %#v %v", state, err)
	}
	state, err = svc.MarkRead(ctx, "reader", chat.ChannelGlobal, msg.ID)
	if err != nil || state.Unread != 0 {
		t.Fatalf("read: %#v %v", state, err)
	}
	if _, err = svc.MarkRead(ctx, "reader", chat.ChannelAlliance, msg.ID); err == nil {
		t.Fatal("non-member advanced alliance cursor")
	}
	if _, err = svc.MarkRead(ctx, "reader", chat.ChannelGlobal, "invented"); err == nil {
		t.Fatal("invented cursor accepted")
	}
}
