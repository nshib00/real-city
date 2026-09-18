package building

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/world"
)

func TestValidatePlacementRequiresTownHall(t *testing.T) {
	err := ValidatePlacement(PlacementInput{
		Type:             TypeDugout,
		Tile:             world.Tile{Coord: world.Coord{X: 1, Y: 1}, Terrain: world.TerrainGrass},
		Footprint:        Footprint{Width: 1, Height: 1},
		RequiresTownHall: true,
		BuildingLimit:    8,
	})
	if err == nil {
		t.Fatal("expected town hall requirement error")
	}
}

func TestRushCompletionCrystalCost(t *testing.T) {
	cases := []struct {
		name      string
		remaining time.Duration
		want      int
	}{
		{name: "done", remaining: 0, want: 0},
		{name: "under three minutes", remaining: 2*time.Minute + 59*time.Second, want: 1},
		{name: "exactly three minutes", remaining: 3 * time.Minute, want: 2},
		{name: "started second block", remaining: 5*time.Minute + 59*time.Second, want: 2},
		{name: "third block", remaining: 6 * time.Minute, want: 3},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := RushCompletionCrystalCost(tc.remaining); got != tc.want {
				t.Fatalf("expected %d, got %d", tc.want, got)
			}
		})
	}
}

func TestValidatePlacementAllowsSingleTownHall(t *testing.T) {
	err := ValidatePlacement(PlacementInput{
		Type:          TypeTownHall,
		Tile:          world.Tile{Coord: world.Coord{X: 0, Y: 0}, Terrain: world.TerrainGrass},
		Footprint:     Footprint{Width: 1, Height: 1},
		BuildingLimit: 8,
	})
	if err != nil {
		t.Fatalf("expected town hall placement to be valid: %v", err)
	}
}

func TestRoadDoesNotUseBuildingLimit(t *testing.T) {
	err := ValidatePlacement(PlacementInput{
		Type:             TypeRoad,
		Tile:             world.Tile{Coord: world.Coord{X: 4, Y: 4}, Terrain: world.TerrainGrass},
		Footprint:        Footprint{Width: 1, Height: 1},
		HasTownHall:      true,
		RequiresTownHall: true,
		BuildingLimit:    1,
		UsedLimit:        1,
	})
	if err != nil {
		t.Fatalf("expected road to ignore building limit: %v", err)
	}
}

func TestValidatePlacementBlocksForestWaterAndMountain(t *testing.T) {
	for _, terrain := range []world.TerrainType{world.TerrainForest, world.TerrainWater, world.TerrainMountain} {
		err := ValidatePlacement(PlacementInput{
			Type:          TypeTownHall,
			Tile:          world.Tile{Coord: world.Coord{X: 0, Y: 0}, Terrain: terrain, ForestDensity: 3},
			Footprint:     Footprint{Width: 1, Height: 1},
			BuildingLimit: 8,
		})
		if err == nil {
			t.Fatalf("expected terrain %s to block placement", terrain)
		}
	}
}

func TestValidatePlacementBlocksRestrictedTerrainOnTargetTile(t *testing.T) {
	err := ValidatePlacement(PlacementInput{
		Type:      TypeTownHall,
		Tile:      world.Tile{Coord: world.Coord{X: 10, Y: 10}, Terrain: world.TerrainRuins},
		Footprint: Footprint{Width: 1, Height: 1},
		BuildingLimit: 8,
	})
	if err == nil {
		t.Fatal("expected restricted terrain on target tile to block placement")
	}
}
