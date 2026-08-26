package building

import (
	"testing"

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

func TestValidatePlacementAllowsSingleTownHall(t *testing.T) {
	err := ValidatePlacement(PlacementInput{
		Type:          TypeTownHall,
		Tile:          world.Tile{Coord: world.Coord{X: 0, Y: 0}, Terrain: world.TerrainGrass},
		Footprint:     Footprint{Width: 2, Height: 2},
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

func TestValidatePlacementBlocksRestrictedTerrainInsideFootprint(t *testing.T) {
	err := ValidatePlacement(PlacementInput{
		Type:      TypeTownHall,
		Tile:      world.Tile{Coord: world.Coord{X: 10, Y: 10}, Terrain: world.TerrainGrass},
		Footprint: Footprint{Width: 2, Height: 2},
		Tiles: []world.Tile{
			{Coord: world.Coord{X: 10, Y: 10}, Terrain: world.TerrainGrass},
			{Coord: world.Coord{X: 11, Y: 10}, Terrain: world.TerrainForest, ForestDensity: 3},
			{Coord: world.Coord{X: 10, Y: 11}, Terrain: world.TerrainGrass},
			{Coord: world.Coord{X: 11, Y: 11}, Terrain: world.TerrainGrass},
		},
		BuildingLimit: 8,
	})
	if err == nil {
		t.Fatal("expected restricted terrain inside footprint to block placement")
	}
}
