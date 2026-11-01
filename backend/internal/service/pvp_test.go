package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func pvpFixture(t *testing.T) (*CombatService, *memory.BuildingRepo, *memory.EconomyRepo, *memory.ActionRepo) {
	t.Helper()
	ctx := context.Background()
	buildings, inventory, actions := memory.NewBuildingRepo(), memory.NewEconomyRepo(), memory.NewActionRepo()
	worlds := memory.NewWorldRepo()
	if _, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkCoord{}); err != nil {
		t.Fatal(err)
	}
	for x := 0; x < 16; x++ {
		for y := 0; y < 16; y++ {
			if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: world.Coord{X: x, Y: y}, Terrain: world.TerrainGrass}); err != nil {
				t.Fatal(err)
			}
		}
	}
	for _, b := range []building.Building{
		{ID: "source", OwnerID: "attacker", Tile: world.Coord{X: 4, Y: 4}},
		{ID: "target", OwnerID: "defender", Tile: world.Coord{X: 6, Y: 4}},
	} {
		b.MapID, b.Type, b.Level, b.State, b.Health, b.Footprint = DefaultWorldID, building.TypeTownHall, 1, building.StateActive, 1000, building.Footprint{Width: 1, Height: 1}
		if err := buildings.Create(ctx, b); err != nil {
			t.Fatal(err)
		}
	}
	inv, _ := inventory.GetInventory(ctx, "attacker", 10000)
	inv.Items[economy.ResourceCoins] = 5000
	inv.Items[economy.ResourceThrowingKnives] = 5
	inv.Items[economy.ResourceBlackpowderBomb] = 5
	if err := inventory.SaveInventory(ctx, inv); err != nil {
		t.Fatal(err)
	}
	s := NewCombatService(NewMonsterService(memory.NewMonsterRepo(), slog.Default()), slog.Default())
	s.SetWeaponDependencies(inventory, actions, nil)
	s.SetPvPDependencies(buildings, worlds, nil)
	s.now = func() time.Time { return time.Date(2026, 10, 30, 10, 0, 0, 0, time.UTC) }
	return s, buildings, inventory, actions
}

func TestBuildingWeaponValidatesTargetAndConsumesOnce(t *testing.T) {
	s, buildings, inventory, _ := pvpFixture(t)
	ctx := context.Background()
	if _, err := s.UseBuildingWeapon(ctx, "source", "attacker", economy.ResourceThrowingKnives, "self-target-key"); err == nil {
		t.Fatal("own building accepted")
	}
	result, err := s.UseBuildingWeapon(ctx, "target", "attacker", economy.ResourceThrowingKnives, "weapon-first-key")
	if err != nil {
		t.Fatal(err)
	}
	if result.Building == nil || result.Building.Health != 920 {
		t.Fatalf("instant hit: %+v", result)
	}
	if _, err := s.UseBuildingWeapon(ctx, "target", "attacker", economy.ResourceThrowingKnives, "weapon-first-key"); err == nil {
		t.Fatal("duplicate accepted")
	}
	if _, err := s.UseBuildingWeapon(ctx, "target", "attacker", economy.ResourceThrowingKnives, "weapon-new-key"); err == nil {
		t.Fatal("cooldown bypassed")
	}
	inv, _ := inventory.GetInventory(ctx, "attacker", 10000)
	if inv.Items[economy.ResourceThrowingKnives] != 4 {
		t.Fatal("failed attack consumed weapon")
	}
	target, _ := buildings.FindByID(ctx, "target")
	target.Tile = world.Coord{X: 80, Y: 80}
	if err := buildings.Update(ctx, target); err != nil {
		t.Fatal(err)
	}
	if _, err := s.UseBuildingWeapon(ctx, "target", "attacker", economy.ResourceBlackpowderBomb, "out-of-range-key"); err == nil {
		t.Fatal("out of range target accepted")
	}
}

func TestBuildingBombFuseAndChangedOwner(t *testing.T) {
	for _, changedOwner := range []bool{false, true} {
		t.Run(map[bool]string{false: "damage", true: "changed_owner"}[changedOwner], func(t *testing.T) {
			s, buildings, _, actions := pvpFixture(t)
			ctx, now := context.Background(), s.now()
			attack, err := s.UseBuildingWeapon(ctx, "target", "attacker", economy.ResourceBlackpowderBomb, "delayed-bomb-key")
			if err != nil {
				t.Fatal(err)
			}
			if attack.Building != nil || attack.DueAt.Sub(now) != 40*time.Second {
				t.Fatal("wrong fuse")
			}
			target, _ := buildings.FindByID(ctx, "target")
			if target.Health != 1000 {
				t.Fatal("damage before fuse")
			}
			pending, _ := s.PendingWeapons(ctx, "attacker")
			if len(pending) != 1 || pending[0].BuildingID != "target" || pending[0].MonsterID != "" {
				t.Fatalf("pending = %+v", pending)
			}
			if changedOwner {
				target.OwnerID = "new-owner"
				if err := buildings.Update(ctx, target); err != nil {
					t.Fatal(err)
				}
			}
			due, err := actions.FetchDue(ctx, attack.DueAt, 10, time.Minute)
			if err != nil || len(due) != 1 {
				t.Fatalf("due = %v, %v", due, err)
			}
			if err := s.ResolveWeapon(ctx, due[0]); err != nil {
				t.Fatal(err)
			}
			target, _ = buildings.FindByID(ctx, "target")
			want := 780
			if changedOwner {
				want = 1000
			}
			if target.Health != want {
				t.Fatalf("health=%d want %d", target.Health, want)
			}
		})
	}
}

func TestSummonedMonsterCostCooldownLimitAndNoLoot(t *testing.T) {
	s, _, inventory, _ := pvpFixture(t)
	ctx, now := context.Background(), s.now()
	rules := catalog.CombatRules()
	for i := 0; i < rules.SummonMaxAlive; i++ {
		s.now = func() time.Time { return now.Add(time.Duration(i*rules.SummonCooldownSeconds) * time.Second) }
		item, err := s.CreateMonster(ctx, player.ID("attacker"), "target", string(rune('a'+i))+"summon-key")
		if err != nil {
			t.Fatal(err)
		}
		if item.CreatorID != "attacker" || item.SpawnID != "" || item.ExpiresAt.Sub(s.now()) != time.Duration(rules.SummonLifetimeSeconds)*time.Second {
			t.Fatalf("monster=%+v", item)
		}
		if len(LootForMonster(item)) != 0 {
			t.Fatal("created monster grants loot")
		}
		if _, err := s.CreateMonster(ctx, "attacker", "target", "cooldown-key"); err == nil {
			t.Fatal("cooldown bypassed")
		}
	}
	s.now = func() time.Time {
		return now.Add(time.Duration(rules.SummonMaxAlive*rules.SummonCooldownSeconds) * time.Second)
	}
	if _, err := s.CreateMonster(ctx, "attacker", "target", "limit-test-key"); err == nil {
		t.Fatal("alive cap bypassed")
	}
	inv, _ := inventory.GetInventory(ctx, "attacker", 10000)
	if inv.Items[economy.ResourceCoins] != 5000-rules.SummonMaxAlive*rules.SummonCostCoins {
		t.Fatalf("coins=%d", inv.Items[economy.ResourceCoins])
	}
	// The cap releases after expiration, even before the worker processes despawn.
	s.now = func() time.Time { return now.Add(time.Duration(rules.SummonLifetimeSeconds+1) * time.Second) }
	if _, err := s.CreateMonster(ctx, "attacker", "target", "after-expiry-key"); err != nil {
		t.Fatal(err)
	}
	if len(LootForMonster(monster.Monster{CreatorID: "attacker", Type: monster.TypeAncientColossus})) != 0 {
		t.Fatal("farming summoned monster")
	}
}
