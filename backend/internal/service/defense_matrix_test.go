package service

import (
	"context"
	"fmt"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"testing"
	"time"
)

func TestEveryDefenseWeaponLevelHonorsAmmoCooldownAndFriendlyTargetsAtSeam(t *testing.T) {
	for _, spec := range catalog.AllBuildings() {
		if !catalog.IsDefenseWeapon(spec.Type) {
			continue
		}
		for _, level := range spec.UpgradeLevels {
			t.Run(fmt.Sprintf("%s/%d", spec.Type, level.Level), func(t *testing.T) {
				ctx := context.Background()
				now := time.Now().UTC()
				buildings := memory.NewBuildingRepo()
				monsters := memory.NewMonsterRepo()
				inventory := memory.NewEconomyRepo()
				stats, ok := catalog.DefenseWeaponLevel(spec.Type, level.Level)
				if !ok {
					t.Fatal("missing defense stats")
				}
				if err := buildings.Create(ctx, building.Building{ID: "weapon", MapID: DefaultWorldID, OwnerID: "owner", Type: spec.Type, Level: level.Level, State: building.StateActive, Health: level.Health, Tile: world.Coord{X: 159, Y: 159}, Footprint: spec.Footprint, CannonEnabled: true}); err != nil {
					t.Fatal(err)
				}
				for _, m := range []monster.Monster{{ID: "enemy", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee, State: monster.StateIdle, Health: 100000, MaxHealth: 100000, Tile: world.Coord{X: 0, Y: 159}, UpdatedAt: now}, {ID: "friendly", MapID: DefaultWorldID, CreatorID: "owner", Type: monster.TypeRoamingMelee, State: monster.StateIdle, Health: 100000, MaxHealth: 100000, Tile: world.Coord{X: 159, Y: 159}, ExpiresAt: now.Add(time.Hour), UpdatedAt: now}} {
					if err := monsters.Create(ctx, m); err != nil {
						t.Fatal(err)
					}
				}
				inv, err := inventory.GetInventory(ctx, "owner", 2000)
				if err != nil {
					t.Fatal(err)
				}
				if stats.Ammo != "" {
					inv.Items[stats.Ammo] = 10
					if err := inventory.SaveInventory(ctx, inv); err != nil {
						t.Fatal(err)
					}
				}
				s := NewCannonService(buildings, monsters, inventory, nil, nil, NewMonsterService(monsters, slog.Default()), nil, nil, slog.Default())
				for _, at := range []time.Time{now, now.Add(stats.Cooldown)} {
					if fired, err := s.Tick(ctx, at, 10); err != nil || fired != 1 {
						t.Fatal("shot", fired, err)
					}
				}
				if fired, err := s.Tick(ctx, now.Add(stats.Cooldown).Add(time.Nanosecond), 10); err != nil || fired != 0 {
					t.Fatal("cooldown bypassed", fired, err)
				}
				enemy, _ := monsters.FindByID(ctx, "enemy")
				friendly, _ := monsters.FindByID(ctx, "friendly")
				if enemy.Health != 100000-2*stats.Damage || friendly.Health != 100000 {
					t.Fatal("wrong damage or friendly fire", enemy.Health, friendly.Health)
				}
				if stats.Ammo != "" {
					after, _ := inventory.GetInventory(ctx, "owner", 2000)
					if after.Items[stats.Ammo] != 8 {
						t.Fatal("wrong ammo cost", after.Items[stats.Ammo])
					}
				}
			})
		}
	}
}
