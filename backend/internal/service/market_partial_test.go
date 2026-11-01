package service

import (
	"context"
	"log/slog"
	"testing"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
)

func TestPartialMarketFillAndCancelRefundOnlyRemainder(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewSocialRepo()
	eco := NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default())
	s := NewMarketService(repo, eco, slog.Default())
	seller := grantTestResources(t, ctx, eco, "seller", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 100})
	buyer := grantTestResources(t, ctx, eco, "buyer", economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: 1000})
	sell, err := s.Create(ctx, "seller", market.SideSell, economy.ResourceWood, 100, 200)
	if err != nil {
		t.Fatal(err)
	}
	buy, err := s.Create(ctx, "buyer", market.SideBuy, economy.ResourceWood, 30, 90)
	if err != nil {
		t.Fatal(err)
	}
	if buy.Status != market.StatusFilled || buy.FilledAmount != 30 {
		t.Fatal(buy)
	}
	partial, err := repo.FindOrder(ctx, sell.ID)
	if err != nil || partial.Status != market.StatusOpen || partial.FilledAmount != 30 {
		t.Fatalf("partial %+v %v", partial, err)
	}
	if _, err := s.Cancel(ctx, "seller", sell.ID); err != nil {
		t.Fatal(err)
	}
	a, _ := eco.Inventory(ctx, "seller")
	b, _ := eco.Inventory(ctx, "buyer")
	if a.Items[economy.ResourceWood] != seller.Items[economy.ResourceWood]-30 || a.Items[economy.ResourceCoins] != seller.Items[economy.ResourceCoins]+50 || b.Items[economy.ResourceCoins] != buyer.Items[economy.ResourceCoins]-64 || b.Items[economy.ResourceWood] != 30 {
		t.Fatal("partial fill or refund lost resources")
	}
}

func TestPartialMarketBuyCancellationAndMultipleMakers(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewSocialRepo()
	eco := NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default())
	s := NewMarketService(repo, eco, slog.Default())
	buyer := grantTestResources(t, ctx, eco, "buyer", economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: 1000})
	for _, id := range []string{"s1", "s2"} {
		grantTestResources(t, ctx, eco, player.ID(id), economy.ResourceAmount{Resource: economy.ResourceStone, Amount: 20})
	}
	buy, err := s.Create(ctx, "buyer", market.SideBuy, economy.ResourceStone, 100, 300)
	if err != nil {
		t.Fatal(err)
	}
	for _, id := range []string{"s1", "s2"} {
		if _, err := s.Create(ctx, player.ID(id), market.SideSell, economy.ResourceStone, 20, 40); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := s.Cancel(ctx, "buyer", buy.ID); err != nil {
		t.Fatal(err)
	}
	after, _ := eco.Inventory(ctx, "buyer")
	if after.Items[economy.ResourceStone] != 40 || after.Items[economy.ResourceCoins] != buyer.Items[economy.ResourceCoins]-135 {
		t.Fatal("buy remainder refund incorrect")
	}
}
