package service

import (
	"context"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
	"sync"
	"testing"
)

func TestMarketMatchTransfersAndRefundsPriceImprovement(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewSocialRepo()
	eco := NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default())
	svc := NewMarketService(repo, eco, slog.Default())
	seller := grantTestResources(t, ctx, eco, "seller", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 5})
	buyer := grantTestResources(t, ctx, eco, "buyer", economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: 1000})
	sell, err := svc.Create(ctx, "seller", market.SideSell, economy.ResourceWood, 5, 100)
	if err != nil {
		t.Fatal(err)
	}
	buy, err := svc.Create(ctx, "buyer", market.SideBuy, economy.ResourceWood, 5, 120)
	if err != nil {
		t.Fatal(err)
	}
	if buy.Status != market.StatusFilled {
		t.Fatal(buy)
	}
	done, _ := repo.FindOrder(ctx, sell.ID)
	if done.Status != market.StatusFilled {
		t.Fatal(done)
	}
	a, _ := eco.Inventory(ctx, "seller")
	b, _ := eco.Inventory(ctx, "buyer")
	if a.Items[economy.ResourceCoins] != seller.Items[economy.ResourceCoins]+95 || b.Items[economy.ResourceCoins] != buyer.Items[economy.ResourceCoins]-106 || b.Items[economy.ResourceWood] != 5 {
		t.Fatal("trade did not settle atomically")
	}
	if _, err = svc.Cancel(ctx, "seller", sell.ID); err == nil {
		t.Fatal("filled order refunded")
	}
}
func TestOnlyOneConcurrentBuyerFillsWholeLot(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewSocialRepo()
	eco := NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default())
	svc := NewMarketService(repo, eco, slog.Default())
	grantTestResources(t, ctx, eco, "seller", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 5})
	if _, err := svc.Create(ctx, "seller", market.SideSell, economy.ResourceWood, 5, 10); err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	results := make(chan market.Order, 2)
	errs := make(chan error, 2)
	for _, p := range []string{"buyer1", "buyer2"} {
		wg.Add(1)
		go func(p string) {
			defer wg.Done()
			v, e := svc.Create(ctx, player.ID(p), market.SideBuy, economy.ResourceWood, 5, 10)
			results <- v
			errs <- e
		}(p)
	}
	wg.Wait()
	close(results)
	close(errs)
	for e := range errs {
		if e != nil {
			t.Fatal(e)
		}
	}
	filled := 0
	for v := range results {
		if v.Status == market.StatusFilled {
			filled++
		}
	}
	if filled != 1 {
		t.Fatal(filled)
	}
}
func TestMatchingFailureRollsBackBothInventories(t *testing.T) {
	ctx := context.Background()
	repo := &failingOrders{SocialRepo: memory.NewSocialRepo()}
	eco := NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default())
	svc := NewMarketService(repo, eco, slog.Default())
	grantTestResources(t, ctx, eco, "seller", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 5})
	if _, err := svc.Create(ctx, "seller", market.SideSell, economy.ResourceWood, 5, 10); err != nil {
		t.Fatal(err)
	}
	before, _ := eco.Inventory(ctx, "buyer")
	sellerBefore, _ := eco.Inventory(ctx, "seller")
	repo.failUpdate = true
	if _, err := svc.Create(ctx, "buyer", market.SideBuy, economy.ResourceWood, 5, 10); err == nil {
		t.Fatal("expected failure")
	}
	after, _ := eco.Inventory(ctx, "buyer")
	sellerAfter, _ := eco.Inventory(ctx, "seller")
	if after.Items[economy.ResourceWood] != before.Items[economy.ResourceWood] || after.Items[economy.ResourceCoins] != before.Items[economy.ResourceCoins] || sellerAfter.Items[economy.ResourceCoins] != sellerBefore.Items[economy.ResourceCoins] {
		t.Fatal("partial settlement escaped rollback")
	}
}
