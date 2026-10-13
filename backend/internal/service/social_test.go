package service

import (
	"context"
	"log/slog"
	"testing"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
)

func TestAllianceCreateDonateAndBuff(t *testing.T) {
	ctx := context.Background()
	economyRepo := memory.NewEconomyRepo()
	socialRepo := memory.NewSocialRepo()
	economyService := NewEconomyService(economyRepo, nil, slog.Default())
	allianceService := NewAllianceService(socialRepo, economyService, slog.Default())

	profile, err := allianceService.Create(ctx, "player-1", "Северный караван")
	if err != nil {
		t.Fatalf("create alliance: %v", err)
	}
	if profile.Alliance.Name != "Северный караван" {
		t.Fatalf("unexpected alliance name %q", profile.Alliance.Name)
	}
	if profile.Self.Role != alliance.RoleLeader {
		t.Fatalf("leader role was not assigned")
	}
	grantTestResources(t, ctx, economyService, "player-1", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 25})

	profile, err = allianceService.Donate(ctx, "player-1", economy.ResourceWood, 25)
	if err != nil {
		t.Fatalf("donate: %v", err)
	}
	if len(profile.Treasury) != 1 || profile.Treasury[0].Amount != 25 {
		t.Fatalf("donation was not written to treasury ledger: %#v", profile.Treasury)
	}

	profile, err = allianceService.UpgradeBuff(ctx, "player-1", "build_speed")
	if err != nil {
		t.Fatalf("upgrade buff: %v", err)
	}
	if len(profile.Buffs) != 1 || profile.Buffs[0].Level != 1 {
		t.Fatalf("buff was not upgraded: %#v", profile.Buffs)
	}
}

func TestChatFlagsModerationAndRestrictsAllianceChannel(t *testing.T) {
	ctx := context.Background()
	socialRepo := memory.NewSocialRepo()
	chatService := NewChatService(socialRepo, socialRepo, slog.Default())

	if _, err := chatService.List(ctx, "player-1", chat.ChannelAlliance, 10); err == nil {
		t.Fatalf("expected alliance channel to require membership")
	}

	msg, err := chatService.Send(ctx, "player-1", chat.ChannelGlobal, "", "смотрите https://example.test")
	if err != nil {
		t.Fatalf("send chat: %v", err)
	}
	if !msg.Flagged {
		t.Fatalf("message with url must be flagged")
	}
}

func TestMarketReservesResourcesAndRefundsOnCancel(t *testing.T) {
	ctx := context.Background()
	economyRepo := memory.NewEconomyRepo()
	socialRepo := memory.NewSocialRepo()
	economyService := NewEconomyService(economyRepo, nil, slog.Default())
	marketService := NewMarketService(socialRepo, economyService, slog.Default())

	before, err := economyService.Inventory(ctx, "player-1")
	if err != nil {
		t.Fatalf("inventory before: %v", err)
	}
	before = grantTestResources(t, ctx, economyService, "player-1", economy.ResourceAmount{Resource: economy.ResourceWood, Amount: 50})
	order, err := marketService.Create(ctx, "player-1", market.SideSell, economy.ResourceWood, 50, 100)
	if err != nil {
		t.Fatalf("create order: %v", err)
	}
	afterCreate, err := economyService.Inventory(ctx, "player-1")
	if err != nil {
		t.Fatalf("inventory after create: %v", err)
	}
	if afterCreate.Items[economy.ResourceWood] != before.Items[economy.ResourceWood]-50 {
		t.Fatalf("sell order did not reserve resource")
	}

	cancelled, err := marketService.Cancel(ctx, "player-1", order.ID)
	if err != nil {
		t.Fatalf("cancel order: %v", err)
	}
	afterCancel, err := economyService.Inventory(ctx, "player-1")
	if err != nil {
		t.Fatalf("inventory after cancel: %v", err)
	}
	if cancelled.Status != market.StatusCancelled {
		t.Fatalf("order was not cancelled")
	}
	if afterCancel.Items[economy.ResourceWood] != before.Items[economy.ResourceWood] {
		t.Fatalf("cancel did not refund reserved resource")
	}
}

var _ player.ID
