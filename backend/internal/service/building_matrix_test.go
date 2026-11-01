package service

import (
	"context"
	"fmt"
	"log/slog"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/world"
	"testing"
	"time"
)

// Exercises real placement/completion/demolition for every catalog type at
// interior, edges and corners. Economy/XP have their own transactional tests.
func TestEveryBuildingPlacementLifecycleAtWorldSeams(t *testing.T) {
	for _, spec := range xpBuildingSpecs() {
		for _, origin := range []world.Coord{{X: 20, Y: 20}, {X: 159, Y: 20}, {X: 20, Y: 159}, {X: 159, Y: 159}, {X: -1, Y: -1}} {
			t.Run(fmt.Sprintf("%s/%d/%d", spec.Type, origin.X, origin.Y), func(t *testing.T) {
				ctx := context.Background()
				repo := memory.NewBuildingRepo()
				worlds := memory.NewWorldRepo()
				s := NewBuildingService(repo, worlds, slog.Default())
				now := time.Now().UTC()
				s.SetNowForTest(func() time.Time { return now })
				if spec.Type != building.TypeTownHall {
					if err := repo.Create(ctx, building.Building{ID: "center", OwnerID: "p", MapID: DefaultWorldID, Type: building.TypeTownHall, Level: 30, State: building.StateActive, Health: 100, Tile: world.Coord{X: 80, Y: 80}, Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
						t.Fatal(err)
					}
				}
				for y := 0; y < spec.Footprint.Height; y++ {
					for x := 0; x < spec.Footprint.Width; x++ {
						coord := world.NormalizeCoord(world.Coord{X: origin.X + x, Y: origin.Y + y})
						terrain := world.TerrainGrass
						ruin := ""
						if spec.Type == building.TypeOilWell {
							terrain = world.TerrainOilWell
						}
						if catalog.IsRuin(spec.Type) {
							terrain = world.TerrainRuins
							ruin = string(spec.Type)
						}
						if _, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(coord)); err != nil {
							t.Fatal(err)
						}
						if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: coord, Terrain: terrain, RuinType: ruin}); err != nil {
							t.Fatal(err)
						}
					}
				}
				item, err := s.Place(ctx, PlaceBuildingInput{PlayerID: "p", Type: spec.Type, Tile: origin})
				if !catalog.CanPlaceDirectly(spec.Type) && !catalog.IsRuin(spec.Type) {
					if err == nil {
						t.Fatal("upgrade-only type placed directly")
					}
					return
				}
				if err != nil {
					t.Fatal(err)
				}
				if item.Tile != world.NormalizeCoord(origin) || len(item.OccupiedTiles()) != spec.Footprint.Width*spec.Footprint.Height {
					t.Fatal("wrong wrapped footprint", item)
				}
				if _, err := s.Place(ctx, PlaceBuildingInput{PlayerID: "other", Type: spec.Type, Tile: origin}); err == nil {
					t.Fatal("occupied footprint accepted")
				}
				if item.CompletesAt != nil {
					if _, err := s.CompleteAt(ctx, item.ID, "p", item.CompletesAt.Add(-time.Nanosecond)); err == nil {
						t.Fatal("completed early")
					}
					item, err = s.CompleteAt(ctx, item.ID, "p", *item.CompletesAt)
					if err != nil {
						t.Fatal(err)
					}
				}
				if item.State != building.StateActive || item.Health != spec.Health {
					t.Fatal("wrong completion", item)
				}
				if err := s.Demolish(ctx, item.ID, "other"); err == nil {
					t.Fatal("enemy demolished without combat")
				}
				if err := s.Demolish(ctx, item.ID, "p"); err != nil {
					t.Fatal(err)
				}
				if _, err := repo.FindByID(ctx, item.ID); err == nil {
					t.Fatal("demolished object persisted")
				}
			})
		}
	}
}

func TestEveryBuildingUpgradeChargesCatalogCostAndReturnsWorkers(t *testing.T) {
	for _, spec := range catalog.AllBuildings() {
		for index := 1; index < len(spec.UpgradeLevels); index++ {
			previous, next := spec.UpgradeLevels[index-1], spec.UpgradeLevels[index]
			t.Run(fmt.Sprintf("%s/%d", spec.Type, next.Level), func(t *testing.T) {
				ctx := withoutStarterPopulationBackfill(WithoutCatchUp(context.Background()))
				repo := memory.NewBuildingRepo()
				inventory := memory.NewEconomyRepo()
				eco := NewEconomyService(inventory, repo, slog.Default())
				s := NewBuildingService(repo, nil, slog.Default())
				s.SetEconomy(eco)
				now := time.Now().UTC()
				s.SetNowForTest(func() time.Time { return now })
				eco.now = func() time.Time { return now }
				before := economy.EmptyInventory("p", now, BaseCoinCapacity)
				for _, r := range economy.AllResourceTypes() {
					before.Items[r] = 100_000_000
				}
				if err := inventory.SaveInventory(ctx, before); err != nil {
					t.Fatal(err)
				}
				if err := repo.Create(ctx, building.Building{ID: "upgrade", MapID: DefaultWorldID, OwnerID: "p", Type: spec.Type, Level: previous.Level, State: building.StateActive, Health: previous.Health, Footprint: spec.Footprint}); err != nil {
					t.Fatal(err)
				}
				item, err := s.UpgradeTo(ctx, "upgrade", "p", spec.Type)
				if err != nil {
					t.Fatal(err)
				}
				if item.Level != next.Level || item.Health != next.Health {
					t.Fatal("wrong upgraded level/health", item)
				}
				if next.BuildDuration > 0 && (item.CompletesAt == nil || item.CompletesAt.Sub(now) != next.BuildDuration) {
					t.Fatal("wrong timer", item)
				}
				after, err := eco.Inventory(ctx, "p")
				if err != nil {
					t.Fatal(err)
				}
				for _, cost := range next.Cost {
					if got, want := after.Items[economy.ResourceType(cost.Resource)], before.Items[economy.ResourceType(cost.Resource)]-cost.Amount; got != want {
						t.Fatalf("%s: %d, want %d", cost.Resource, got, want)
					}
				}
				if item.CompletesAt != nil {
					if after.Items[economy.ResourcePopulation] != before.Items[economy.ResourcePopulation]-next.Population {
						t.Fatal("workers not reserved")
					}
					if _, err := s.CompleteAt(ctx, item.ID, "p", *item.CompletesAt); err != nil {
						t.Fatal(err)
					}
				}
				after, err = eco.Inventory(ctx, "p")
				if err != nil {
					t.Fatal(err)
				}
				if after.Items[economy.ResourcePopulation] != before.Items[economy.ResourcePopulation] {
					t.Fatal("workers not returned")
				}
			})
		}
	}
}
