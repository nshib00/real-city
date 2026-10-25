package service

import (
	"context"
	"log/slog"
	"slices"
	"sync"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func TestMonsterAttackPublishesActualDamageOnKillingBlow(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewMonsterRepo()
	item := monster.Monster{ID: "low-health", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee,
		State: monster.StateIdle, Tile: world.Coord{X: 3, Y: 3}, Health: 12, MaxHealth: 100}
	if err := repo.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	svc := NewMonsterService(repo, slog.Default())
	bus := NewEventBus(8)
	svc.SetEventBus(bus)
	events := bus.Subscribe(ctx)
	if _, _, err := svc.Attack(ctx, item.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	for {
		select {
		case event := <-events:
			if event.Type != EventMonsterDied {
				continue
			}
			payload, ok := event.Payload.(MonsterPayload)
			if !ok || payload.Damage != 12 || payload.Source != "player" {
				t.Fatalf("unexpected hit event: %#v", event)
			}
			return
		case <-time.After(time.Second):
			t.Fatal("missing monster hit event")
		}
	}
}

func TestEarlyMonsterLootTables(t *testing.T) {
	tests := []struct {
		name    string
		kind    monster.Type
		options []lootOption
		want    []lootOption
	}{
		{
			name:    "бродячий налетчик",
			kind:    monster.TypeRoamingMelee,
			options: roamingMeleeLootOptions,
			want: []lootOption{
				{resource: economy.ResourceCoins, weight: 42, min: 55, max: 75},
				{resource: economy.ResourceWood, weight: 25, min: 18, max: 28},
				{resource: economy.ResourceRope, weight: 20, min: 2, max: 4},
				{resource: economy.ResourceTools, weight: 8, min: 1, max: 1},
				{resource: economy.ResourceExplosives, weight: 5, min: 1, max: 1},
			},
		},
		{
			name:    "страж залежи",
			kind:    monster.TypeResourceGuardian,
			options: resourceGuardianLootOptions,
			want: []lootOption{
				{resource: economy.ResourceCoins, weight: 30, min: 100, max: 140},
				{resource: economy.ResourceStone, weight: 25, min: 9, max: 15},
				{resource: economy.ResourceFiber, weight: 14, min: 3, max: 5},
				{resource: economy.ResourceStoneBlock, weight: 10, min: 3, max: 6},
				{resource: economy.ResourceTools, weight: 12, min: 1, max: 2},
				{resource: economy.ResourceExplosives, weight: 7, min: 1, max: 1},
				{resource: economy.ResourceIronIngot, weight: 2, min: 1, max: 2},
			},
		},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if !slices.Equal(test.options, test.want) {
				t.Fatalf("loot options: got %#v, want %#v", test.options, test.want)
			}
			total := 0
			for _, option := range test.options {
				total += option.weight
			}
			if total != 100 {
				t.Fatalf("loot weights sum to %d, want 100", total)
			}
			for range 1000 {
				loot := LootForMonster(monster.Monster{Type: test.kind})
				if len(loot) != 1 {
					t.Fatalf("expected one loot item, got %#v", loot)
				}
				found := false
				for _, option := range test.options {
					if loot[0].Resource == option.resource {
						found = true
						if loot[0].Amount < option.min || loot[0].Amount > option.max {
							t.Fatalf("invalid amount for %s: %d", option.resource, loot[0].Amount)
						}
					}
				}
				if !found {
					t.Fatalf("unknown loot resource: %s", loot[0].Resource)
				}
			}
		})
	}
}

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

	killed, drop, err := service.Attack(ctx, item.ID, player.ID("p1"))
	if err != nil {
		t.Fatalf("attack monster: %v", err)
	}
	if killed.State != monster.StateDead {
		t.Fatalf("expected dead monster, got %s", killed.State)
	}
	if drop == nil || drop.MonsterID != item.ID || len(drop.Items) != 1 {
		t.Fatalf("expected persisted loot in attack result, got %#v", drop)
	}
	drops, err := service.ListLoot(ctx, world.Coord{X: item.Tile.X, Y: item.Tile.Y}, 1)
	if err != nil {
		t.Fatalf("list loot: %v", err)
	}
	if len(drops) != 1 {
		t.Fatalf("expected one loot drop, got %d", len(drops))
	}
	if drops[0].ID != drop.ID {
		t.Fatalf("expected returned loot to match map drop, got %#v", drops[0])
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

func TestMonsterDeathRejectsStaleMovementAndSecondKill(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewMonsterRepo()
	service := NewMonsterService(repo, slog.Default())
	previous, err := repo.FindByID(ctx, "monster_roamer_1")
	if err != nil {
		t.Fatal(err)
	}
	previous.Health = 20
	if err := repo.Update(ctx, previous); err != nil {
		t.Fatal(err)
	}
	staleMovement := previous
	staleMovement.Tile.X++
	staleMovement.UpdatedAt = previous.UpdatedAt.Add(time.Second)

	dead, drop, err := service.Attack(ctx, previous.ID, player.ID("p1"))
	if err != nil || dead.State != monster.StateDead || drop == nil {
		t.Fatalf("expected killing blow and loot, got monster=%#v drop=%#v err=%v", dead, drop, err)
	}
	applied, err := repo.UpdateIfCurrent(ctx, previous, staleMovement)
	if err != nil || applied {
		t.Fatalf("stale movement revived the monster: applied=%v err=%v", applied, err)
	}
	stored, err := repo.FindByID(ctx, previous.ID)
	if err != nil || stored.State != monster.StateDead || stored.Health != 0 || stored.Tile != previous.Tile {
		t.Fatalf("monster changed after death: %#v, err=%v", stored, err)
	}
	if _, _, err := service.Attack(ctx, previous.ID, player.ID("p2")); err == nil {
		t.Fatal("second kill succeeded")
	}
	drops, err := service.ListLoot(ctx, previous.Tile, 1)
	if err != nil || len(drops) != 1 {
		t.Fatalf("expected one drop, got %#v, err=%v", drops, err)
	}
}

func TestConcurrentMonsterKillsCreateOneLootDrop(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewMonsterRepo()
	service := NewMonsterService(repo, slog.Default())
	item, err := repo.FindByID(ctx, "monster_roamer_1")
	if err != nil {
		t.Fatal(err)
	}
	item.Health = 20
	if err := repo.Update(ctx, item); err != nil {
		t.Fatal(err)
	}
	start := make(chan struct{})
	var group sync.WaitGroup
	results := make(chan error, 2)
	for range 2 {
		group.Add(1)
		go func() {
			defer group.Done()
			<-start
			_, _, err := service.Attack(ctx, item.ID, player.ID("p1"))
			results <- err
		}()
	}
	close(start)
	group.Wait()
	close(results)
	successes := 0
	for err := range results {
		if err == nil {
			successes++
		}
	}
	drops, err := service.ListLoot(ctx, item.Tile, 1)
	if err != nil || successes != 1 || len(drops) != 1 {
		t.Fatalf("expected one successful kill and one drop: successes=%d drops=%#v err=%v", successes, drops, err)
	}
}

func TestMonsterListIncludesWrappedEdge(t *testing.T) {
	service := NewMonsterService(memory.NewMonsterRepo(), slog.Default())
	items, err := service.List(context.Background(), world.Coord{X: 158, Y: 2}, 15)
	if err != nil {
		t.Fatal(err)
	}
	for _, item := range items {
		if item.ID == "monster_roamer_1" {
			return
		}
	}
	t.Fatal("monster near opposite map edge is missing")
}

func TestMonsterLootListIncludesWrappedEdge(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewMonsterRepo()
	service := NewMonsterService(repo, slog.Default())
	item := monster.LootDrop{ID: "edge-loot", MapID: DefaultWorldID, Tile: world.Coord{X: 0, Y: 1}, CreatedAt: time.Now()}
	if err := repo.CreateLootDrop(ctx, item); err != nil {
		t.Fatal(err)
	}
	items, err := service.ListLoot(ctx, world.Coord{X: 159, Y: 1}, 2)
	if err != nil || len(items) != 1 || items[0].ID != item.ID {
		t.Fatalf("expected wrapped loot, got items=%#v err=%v", items, err)
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
