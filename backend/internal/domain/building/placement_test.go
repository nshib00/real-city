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

func TestValidatePlacementRejectsNonSingleTileFootprint(t *testing.T) {
	for _, footprint := range []Footprint{{}, {Width: 2, Height: 1}, {Width: 1, Height: 2}} {
		err := ValidatePlacement(PlacementInput{
			Type: TypeTownHall, Tile: world.Tile{Coord: world.Coord{X: 1, Y: 1}, Terrain: world.TerrainGrass},
			Footprint: footprint, BuildingLimit: 8,
		})
		if err == nil {
			t.Fatalf("accepted footprint %+v", footprint)
		}
	}
}

func TestValidatePlacementRespectsLegacyOccupiedTiles(t *testing.T) {
	err := ValidatePlacement(PlacementInput{
		Type:      TypeTownHall,
		Tile:      world.Tile{Coord: world.Coord{X: 2, Y: 1}, Terrain: world.TerrainGrass},
		Footprint: Footprint{Width: 1, Height: 1}, BuildingLimit: 8,
		Existing: []Building{{Type: TypeDugout, State: StateActive, Tile: world.Coord{X: 1, Y: 1}, Footprint: Footprint{Width: 2, Height: 1}}},
	})
	if err == nil {
		t.Fatal("legacy building's second tile was treated as free")
	}
}

func TestRoadDoesNotUseBuildingLimit(t *testing.T) {
	for _, buildingType := range []Type{TypeRoad, TypeStandardRoad, TypePavedRoad} {
		err := ValidatePlacement(PlacementInput{
			Type:             buildingType,
			Tile:             world.Tile{Coord: world.Coord{X: 4, Y: 4}, Terrain: world.TerrainGrass},
			Footprint:        Footprint{Width: 1, Height: 1},
			HasTownHall:      true,
			RequiresTownHall: true,
			BuildingLimit:    1,
			UsedLimit:        1,
		})
		if err != nil {
			t.Fatalf("expected road %s to ignore building limit: %v", buildingType, err)
		}
	}
}

func TestWallsDoNotUseBuildingLimit(t *testing.T) {
	for _, buildingType := range []Type{TypeWoodenWall, TypeStoneWall, TypeConcreteWall, TypeModernWall} {
		err := ValidatePlacement(PlacementInput{
			Type:             buildingType,
			Tile:             world.Tile{Coord: world.Coord{X: 4, Y: 4}, Terrain: world.TerrainGrass},
			Footprint:        Footprint{Width: 1, Height: 1},
			HasTownHall:      true,
			RequiresTownHall: true,
			BuildingLimit:    1,
			UsedLimit:        1,
		})
		if err != nil {
			t.Fatalf("expected wall %s to ignore building limit: %v", buildingType, err)
		}
	}
}

func TestTrapSharesRoadButCannotOverlapAnotherTrapOrBuilding(t *testing.T) {
	tile := world.Tile{Coord: world.Coord{X: 4, Y: 4}, Terrain: world.TerrainGrass}
	for _, existing := range []struct {
		kind    Type
		allowed bool
	}{
		{TypeRoad, true}, {TypeDefenseResinSnare, false}, {TypeDugout, false},
	} {
		err := ValidatePlacement(PlacementInput{Type: TypeDefenseStakes, Tile: tile,
			Footprint: Footprint{Width: 1, Height: 1}, Existing: []Building{{Type: existing.kind, Tile: tile.Coord}},
			HasTownHall: true, RequiresTownHall: true, BuildingLimit: 1, UsedLimit: 1})
		if (err == nil) != existing.allowed {
			t.Fatalf("existing %s: allowed=%t err=%v", existing.kind, existing.allowed, err)
		}
	}
}

func TestUsedBuildingLimitIgnoresRoadsWallsAndRuins(t *testing.T) {
	buildings := []Building{
		{Type: TypeDugout, State: StateActive},
		{Type: TypeTower, State: StateBuilding},
		{Type: TypeRoad, State: StateActive},
		{Type: TypeWoodenWall, State: StateActive},
		{Type: TypeModernWall, State: StateBuilding},
		{Type: TypeMarket, State: StateRuined},
	}

	if got := UsedBuildingLimit(buildings); got != 2 {
		t.Fatalf("expected only ordinary non-ruined buildings to use limit, got %d", got)
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
		Type:          TypeTownHall,
		Tile:          world.Tile{Coord: world.Coord{X: 10, Y: 10}, Terrain: world.TerrainRuins},
		Footprint:     Footprint{Width: 1, Height: 1},
		BuildingLimit: 8,
	})
	if err == nil {
		t.Fatal("expected restricted terrain on target tile to block placement")
	}
}
