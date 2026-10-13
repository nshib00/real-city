package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

func TestAdminCoinsBypassCapacityOnSpendAndAdd(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, 10, 12, 12, 0, 0, 0, time.UTC)
	players := memory.NewPlayerRepo()
	admin := player.Player{
		ID:           "admin",
		Email:        "admin@example.com",
		Name:         "Test Admin",
		PasswordHash: "hash",
		Status:       player.StatusActive,
		Role:         player.RoleAdmin,
		Profile:      player.DefaultProfile("Test Admin", now),
		CreatedAt:    now,
		UpdatedAt:    now,
	}
	if err := players.Create(ctx, admin); err != nil {
		t.Fatal(err)
	}

	repo := memory.NewEconomyRepo()
	service := NewEconomyService(repo, nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetPlayers(players)

	const startingCoins = 1 << 32
	if err := repo.SaveInventory(ctx, economy.Inventory{
		PlayerID:     string(admin.ID),
		CoinCapacity: BaseCoinCapacity,
		Items: map[economy.ResourceType]int{
			economy.ResourceCoins: startingCoins,
		},
		UpdatedAt: now,
	}); err != nil {
		t.Fatal(err)
	}

	afterSpend, err := service.Spend(ctx, admin.ID, []economy.ResourceAmount{{Resource: economy.ResourceCoins, Amount: 125}}, "test:admin_spend")
	if err != nil {
		t.Fatal(err)
	}
	if afterSpend.Items[economy.ResourceCoins] != startingCoins-125 {
		t.Fatalf("admin coins should only decrease by spend amount, got %d", afterSpend.Items[economy.ResourceCoins])
	}
	if !afterSpend.BypassCoinCapacity {
		t.Fatal("expected admin inventory to bypass coin capacity")
	}

	afterAdd, overflow, err := service.Add(ctx, admin.ID, []economy.ResourceAmount{{Resource: economy.ResourceCoins, Amount: 25}}, "test:admin_add")
	if err != nil {
		t.Fatal(err)
	}
	if len(overflow) != 0 {
		t.Fatalf("admin coins should not overflow, got %#v", overflow)
	}
	if afterAdd.Items[economy.ResourceCoins] != startingCoins-100 {
		t.Fatalf("admin coins should not be capped after add, got %d", afterAdd.Items[economy.ResourceCoins])
	}
}

func TestUserCoinsStillRespectCapacity(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, 10, 12, 12, 0, 0, 0, time.UTC)
	players := memory.NewPlayerRepo()
	user := player.Player{
		ID:           "user",
		Email:        "user@example.com",
		Name:         "Regular User",
		PasswordHash: "hash",
		Status:       player.StatusActive,
		Role:         player.RoleUser,
		Profile:      player.DefaultProfile("Regular User", now),
		CreatedAt:    now,
		UpdatedAt:    now,
	}
	if err := players.Create(ctx, user); err != nil {
		t.Fatal(err)
	}

	repo := memory.NewEconomyRepo()
	service := NewEconomyService(repo, nil, slog.New(slog.NewTextHandler(io.Discard, nil)))
	service.SetPlayers(players)

	if err := repo.SaveInventory(ctx, economy.Inventory{
		PlayerID:     string(user.ID),
		CoinCapacity: BaseCoinCapacity,
		Items: map[economy.ResourceType]int{
			economy.ResourceCoins: 1900,
		},
		UpdatedAt: now,
	}); err != nil {
		t.Fatal(err)
	}

	inventory, overflow, err := service.Add(ctx, user.ID, []economy.ResourceAmount{{Resource: economy.ResourceCoins, Amount: 250}}, "test:user_add")
	if err != nil {
		t.Fatal(err)
	}
	if inventory.Items[economy.ResourceCoins] != BaseCoinCapacity {
		t.Fatalf("user coins should be capped at %d, got %d", BaseCoinCapacity, inventory.Items[economy.ResourceCoins])
	}
	if len(overflow) != 1 || overflow[0].Amount != 150 {
		t.Fatalf("expected 150 coin overflow, got %#v", overflow)
	}
	if inventory.BypassCoinCapacity {
		t.Fatal("regular user inventory should not bypass coin capacity")
	}
}
