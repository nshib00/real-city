package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func TestMonsterDeathCreatesPublicLootDrop(t *testing.T) {
	ctx := context.Background()
	monsterRepo := memory.NewMonsterRepo()
	buildingRepo := memory.NewBuildingRepo()
	economyRepo := memory.NewEconomyRepo()
	economyService := NewEconomyService(economyRepo, buildingRepo, slog.Default())
	service := NewMonsterService(monsterRepo, slog.Default())
	service.SetEconomy(economyService)

	item, err := monsterRepo.FindByID(ctx, "monster_roamer_1")
	if err != nil {
		t.Fatal(err)
	}
	item.Health = 20
	if err := monsterRepo.Update(ctx, item); err != nil {
		t.Fatal(err)
	}

	killed, rewards, err := service.Attack(ctx, item.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("attack monster: %v", err)
	}
	if killed.State != monster.StateDead {
		t.Fatalf("expected dead monster, got %s", killed.State)
	}
	if len(rewards) != 0 {
		t.Fatalf("expected loot to stay on map, got immediate rewards: %#v", rewards)
	}
	drops, err := service.ListLoot(ctx, world.Coord{X: item.Tile.X, Y: item.Tile.Y}, 1)
	if err != nil {
		t.Fatalf("list loot: %v", err)
	}
	if len(drops) != 1 {
		t.Fatalf("expected one loot drop, got %d", len(drops))
	}
	if len(drops[0].Items) != 1 {
		t.Fatalf("expected exactly one ordinary loot item, got %#v", drops[0].Items)
	}
	_, inventory, err := service.ClaimLoot(ctx, drops[0].ID, player.ID("p2"))
	if err != nil {
		t.Fatalf("claim loot: %v", err)
	}
	claimed := drops[0].Items[0]
	if inventory.Items[claimed.Resource] < claimed.Amount {
		t.Fatalf("expected claimed resource in inventory, got item=%#v inventory=%#v", claimed, inventory.Items)
	}
	if _, _, err := service.ClaimLoot(ctx, drops[0].ID, player.ID("p3")); err == nil {
		t.Fatal("expected second claim to fail")
	}
}

func TestMonsterDeathSchedulesSourceSpawnPoint(t *testing.T) {
	ctx := context.Background()
	monsterRepo := memory.NewMonsterRepo()
	service := NewMonsterService(monsterRepo, slog.Default())
	now := time.Date(2026, 10, 12, 12, 0, 0, 0, time.UTC)
	service.now = func() time.Time { return now }

	item, err := monsterRepo.FindByID(ctx, "monster_roamer_1")
	if err != nil {
		t.Fatal(err)
	}
	item.Health = 20
	if err := monsterRepo.Update(ctx, item); err != nil {
		t.Fatal(err)
	}
	if _, _, err := service.Attack(ctx, item.ID, player.ID("p1")); err != nil {
		t.Fatalf("attack monster: %v", err)
	}
	spawns, err := monsterRepo.ListSpawnPoints(ctx, DefaultWorldID)
	if err != nil {
		t.Fatal(err)
	}
	for _, spawn := range spawns {
		if spawn.ID != item.SpawnID {
			continue
		}
		delay := spawn.NextSpawnAt.Sub(now)
		if delay < time.Minute || delay > 2*time.Minute {
			t.Fatalf("expected 1-2 minute respawn delay, got %s", delay)
		}
		return
	}
	t.Fatal("source spawn point was not found")
}
