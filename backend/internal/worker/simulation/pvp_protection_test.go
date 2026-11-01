package simulation

import (
	"context"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"testing"
	"time"
)

func TestOfflineProtectionBlocksCreatedMonstersButNotWildOnes(t *testing.T) {
	for _, creator := range []string{"attacker", ""} {
		t.Run("creator="+creator, func(t *testing.T) {
			ctx := context.Background()
			now := time.Now().UTC()
			players := memory.NewPlayerRepo()
			buildings := memory.NewBuildingRepo()
			monsters := memory.NewMonsterRepo()
			if err := players.Create(ctx, player.Player{ID: "owner", Name: "Owner", Email: "owner@example.invalid", Status: player.StatusActive, CreatedAt: now.Add(-time.Hour)}); err != nil {
				t.Fatal(err)
			}
			if err := buildings.Create(ctx, building.Building{ID: "target", MapID: service.DefaultWorldID, OwnerID: "owner", Type: building.TypeDugout, Level: 1, State: building.StateActive, Health: 100, Tile: world.Coord{X: 0, Y: 10}, Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
				t.Fatal(err)
			}
			if err := monsters.Create(ctx, monster.Monster{ID: "monster", MapID: service.DefaultWorldID, Type: monster.TypeRoamingMelee, CreatorID: creator, ExpiresAt: now.Add(time.Hour), State: monster.StateAggro, Health: 100, MaxHealth: 100, Damage: 18, Tile: world.Coord{X: 159, Y: 10}, AttackRange: 1, AggroRadius: 5, AttackCooldown: time.Second, UpdatedAt: now.Add(-time.Hour)}); err != nil {
				t.Fatal(err)
			}
			bs := service.NewBuildingService(buildings, nil, slog.Default())
			bs.SetPvPProtection(players)
			ai := NewMonsterAI(monsters, buildings, nil, nil, slog.Default())
			ai.SetBuildingService(bs)
			if _, err := ai.Tick(ctx, now, 1); err != nil {
				t.Fatal(err)
			}
			target, err := buildings.FindByID(ctx, "target")
			if err != nil {
				t.Fatal(err)
			}
			want := 100
			if creator == "" {
				want = 82
			}
			if target.Health != want {
				t.Fatal("wrong offline protection", target.Health, want)
			}
		})
	}
}
