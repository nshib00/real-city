package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
)

func TestPlayerWeaponFusesFollowPowerProgression(t *testing.T) {
	cases := []struct {
		resource economy.ResourceType
		fuse     time.Duration
	}{
		{economy.ResourceThrowingKnives, 0},
		{economy.ResourceHuntingTraps, 15 * time.Second},
		{economy.ResourceBlackpowderBomb, 40 * time.Second},
		{economy.ResourceFirebomb, 2 * time.Minute},
		{economy.ResourceShapedCharge, 5 * time.Minute},
		{economy.ResourceShockCharge, 15 * time.Minute},
		{economy.ResourceSiegeMine, 20 * time.Minute},
		{economy.ResourceBreachBomb, 30 * time.Minute},
		{economy.ResourceResonanceCharge, 45 * time.Minute},
	}
	for _, test := range cases {
		spec, found := catalog.PlayerWeaponByResource(test.resource)
		if !found || spec.Fuse != test.fuse {
			t.Errorf("%s fuse = %v, found = %t; want %v", test.resource, spec.Fuse, found, test.fuse)
		}
	}
}

func TestPlayerWeaponsConsumeOnceAndResolveAtFuse(t *testing.T) {
	ctx := context.Background()
	monsters := memory.NewMonsterRepo()
	inventoryRepo := memory.NewEconomyRepo()
	actions := memory.NewActionRepo()
	combat := NewCombatService(NewMonsterService(monsters, slog.Default()), slog.Default())
	combat.SetWeaponDependencies(inventoryRepo, actions, nil)
	now := time.Date(2026, 10, 24, 12, 0, 0, 0, time.UTC)
	combat.now = func() time.Time { return now }
	owner := player.ID("weapon-owner")
	inventory, err := inventoryRepo.GetInventory(ctx, owner, 2000)
	if err != nil {
		t.Fatal(err)
	}
	inventory.Items[economy.ResourceThrowingKnives] = 2
	inventory.Items[economy.ResourceBlackpowderBomb] = 1
	if err := inventoryRepo.SaveInventory(ctx, inventory); err != nil {
		t.Fatal(err)
	}

	instant, err := combat.UseWeapon(ctx, monster.ID("monster_roamer_1"), owner, economy.ResourceThrowingKnives, "instant-weapon-001")
	if err != nil {
		t.Fatal(err)
	}
	if instant.Monster == nil || instant.Monster.Health != 280 || !instant.DueAt.Equal(now) {
		t.Fatalf("instant hit = %#v", instant)
	}
	if _, err := combat.UseWeapon(ctx, monster.ID("monster_roamer_1"), owner, economy.ResourceThrowingKnives, "instant-weapon-001"); err == nil {
		t.Fatal("duplicate request was accepted")
	}
	inventory, _ = inventoryRepo.GetInventory(ctx, owner, 2000)
	if inventory.Items[economy.ResourceThrowingKnives] != 1 {
		t.Fatalf("duplicate spent a knife: %v", inventory.Items[economy.ResourceThrowingKnives])
	}

	delayed, err := combat.UseWeapon(ctx, monster.ID("monster_roamer_1"), owner, economy.ResourceBlackpowderBomb, "delayed-weapon-01")
	if err != nil {
		t.Fatal(err)
	}
	if delayed.Monster != nil || delayed.DueAt.Sub(now) != 40*time.Second {
		t.Fatalf("delayed attack = %#v", delayed)
	}
	due, err := actions.FetchDue(ctx, now.Add(39*time.Second), 10, time.Minute)
	if err != nil || len(due) != 0 {
		t.Fatalf("early actions = %v, %v", due, err)
	}
	before, _ := monsters.FindByID(ctx, "monster_roamer_1")
	if before.Health != 280 {
		t.Fatalf("damage before fuse: %d", before.Health)
	}
	due, err = actions.FetchDue(ctx, now.Add(40*time.Second), 10, time.Minute)
	if err != nil || len(due) != 1 {
		t.Fatalf("due actions = %v, %v", due, err)
	}
	if err := combat.ResolveWeapon(ctx, due[0]); err != nil {
		t.Fatal(err)
	}
	if err := actions.MarkDone(ctx, due[0].ID, now.Add(40*time.Second)); err != nil {
		t.Fatal(err)
	}
	after, _ := monsters.FindByID(ctx, "monster_roamer_1")
	if after.Health != 60 {
		t.Fatalf("damage after fuse: %d", after.Health)
	}
	inventory, _ = inventoryRepo.GetInventory(ctx, owner, 2000)
	if inventory.Items[economy.ResourceBlackpowderBomb] != 0 {
		t.Fatal("bomb was not spent")
	}
}

func TestPlayerWeaponCanHitWithoutNearbyOwnedBuilding(t *testing.T) {
	ctx := context.Background()
	monsters := memory.NewMonsterRepo()
	inventoryRepo := memory.NewEconomyRepo()
	combat := NewCombatService(NewMonsterService(monsters, slog.Default()), slog.Default())
	combat.SetWeaponDependencies(inventoryRepo, memory.NewActionRepo(), nil)
	owner := player.ID("distant-owner")
	inventory, _ := inventoryRepo.GetInventory(ctx, owner, 2000)
	inventory.Items[economy.ResourceThrowingKnives] = 1
	if err := inventoryRepo.SaveInventory(ctx, inventory); err != nil {
		t.Fatal(err)
	}
	attack, err := combat.UseWeapon(ctx, "monster_roamer_1", owner, economy.ResourceThrowingKnives, "distant-weapon-01")
	if err != nil {
		t.Fatalf("attack without owned buildings: %v", err)
	}
	if attack.Monster == nil || attack.Monster.Health != 280 {
		t.Fatalf("attack did not damage monster: %#v", attack)
	}
	inventory, _ = inventoryRepo.GetInventory(ctx, owner, 2000)
	if inventory.Items[economy.ResourceThrowingKnives] != 0 {
		t.Fatal("attack did not spend weapon")
	}
}
