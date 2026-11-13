package simulation

import (
	"context"
	"fmt"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
)

// This scenario is a reproducible baseline, not a balance assertion: one
// monster starts exactly at its aggro radius from an undefended 400 HP target.
func TestMonsterThreatBaselineAgainstUndefendedBuilding(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, time.November, 14, 12, 0, 0, 0, time.UTC)

	for _, spec := range catalog.MonsterSpecs() {
		t.Run(string(spec.Type), func(t *testing.T) {
			monsters, buildings := memory.NewMonsterRepo(), memory.NewBuildingRepo()
			buildingTile := world.Coord{X: 40, Y: 40}
			item := monster.Monster{
				ID: "baseline-" + monster.ID(spec.Type), MapID: "dev-world", Type: spec.Type,
				State:    monster.StateWandering,
				Tile:     world.Coord{X: buildingTile.X + spec.AggroRadius, Y: buildingTile.Y},
				HomeTile: world.Coord{X: buildingTile.X + spec.AggroRadius, Y: buildingTile.Y},
				Health:   spec.MaxHealth, MaxHealth: spec.MaxHealth, Damage: spec.Damage,
				SpeedTiles: spec.SpeedTiles, AggroRadius: spec.AggroRadius,
				AttackRange: spec.AttackRange, AttackCooldown: spec.AttackCooldown,
				LastMovedAt: now.Add(-time.Hour), UpdatedAt: now.Add(-time.Hour), CreatedAt: now.Add(-time.Hour),
			}
			if err := monsters.Create(ctx, item); err != nil {
				t.Fatal(err)
			}
			if err := buildings.Create(ctx, building.Building{
				ID: "baseline-target", MapID: "dev-world", OwnerID: "baseline-player",
				Type: building.TypeTownHall, State: building.StateActive,
				Tile: buildingTile, Health: 400, CreatedAt: now, UpdatedAt: now,
			}); err != nil {
				t.Fatal(err)
			}

			ai := NewMonsterAI(monsters, buildings, nil, nil, slog.Default())
			firstHit := time.Duration(-1)
			lastHit := time.Duration(-1)
			var attacks int
			for elapsed := time.Duration(0); elapsed <= 30*time.Minute; elapsed += time.Second {
				if _, err := ai.Tick(ctx, now.Add(elapsed), 10); err != nil {
					t.Fatal(err)
				}
				target, err := buildings.FindByID(ctx, "baseline-target")
				if err != nil {
					t.Fatal(err)
				}
				if target.Health < 400-attacks*spec.Damage {
					attacks++
					if firstHit < 0 {
						firstHit = elapsed
					}
					lastHit = elapsed
				}
				if target.State == building.StateRuined {
					pathLength := max(0, spec.AggroRadius-spec.AttackRange)
					t.Logf("damage=%d cooldown=%s first_hit=%s destroy=%s attacks=%d path_length=%d target_switches=0",
						spec.Damage, spec.AttackCooldown, firstHit, elapsed, attacks, pathLength)
					return
				}
			}
			t.Fatalf("building survived baseline window: hp/damage/cooldown=%d/%d/%s, attacks=%d, last_hit=%s", 400, spec.Damage, spec.AttackCooldown, attacks, lastHit)
		})
	}
}

func BenchmarkMonsterPathSearchBaseline(b *testing.B) {
	ai := NewMonsterAI(nil, memory.NewBuildingRepo(), nil, nil, slog.Default())
	from, to := world.Coord{X: 40, Y: 40}, world.Coord{X: 60, Y: 60}
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		if _, err := ai.nextPassablePath(context.Background(), from, to, 1, 1, make(map[world.ChunkCoord]world.Chunk)); err != nil {
			b.Fatal(err)
		}
	}
}

// BenchmarkMonsterPathSearchCrowd measures 25 same-tick route requests around
// a dense wall with one opening, approximating a coordinated spawn group.
func BenchmarkMonsterPathSearchCrowd(b *testing.B) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	for y := 28; y <= 52; y++ {
		if y == 40 {
			continue
		}
		if err := buildings.Create(ctx, building.Building{
			ID: building.ID(fmt.Sprintf("crowd-wall-%d", y)), MapID: "dev-world", Type: building.TypeStoneWall,
			State: building.StateActive, Tile: world.Coord{X: 50, Y: y}, Health: 100,
		}); err != nil {
			b.Fatal(err)
		}
	}
	ai := NewMonsterAI(nil, buildings, nil, nil, slog.Default())
	starts := make([]world.Coord, 25)
	for i := range starts {
		starts[i] = world.Coord{X: 40, Y: 30 + i}
	}
	chunkCache, buildingCache := make(map[world.ChunkCoord]world.Chunk), newTickBuildingCache(buildings)
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		for _, from := range starts {
			if _, err := ai.nextPassablePathCached(ctx, from, world.Coord{X: 60, Y: 40}, 1, 1, false, chunkCache, buildingCache); err != nil {
				b.Fatal(err)
			}
		}
		buildingCache.clear()
	}
}
