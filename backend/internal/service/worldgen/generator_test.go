package worldgen

import (
	"testing"

	"real-city/backend/internal/domain/world"
)

func TestTerrainKeepsRiversAndMountainsSparse(t *testing.T) {
	generator := New("test-world", 20260727, 10)
	var water int
	var mountain int
	var ruins int
	var stone int
	var total int

	for y := -192; y < 192; y++ {
		for x := -192; x < 192; x++ {
			tile := generator.Tile(world.Coord{X: x, Y: y})
			if tile.SafeZone {
				continue
			}
			total++
			switch tile.Terrain {
			case world.TerrainWater:
				water++
			case world.TerrainMountain:
				mountain++
			case world.TerrainRuins:
				ruins++
			case "stone":
				stone++
			}
		}
	}

	if water*100 > total*4 {
		t.Fatalf("water terrain is too dense: %d/%d", water, total)
	}
	if mountain*100 > total*4 {
		t.Fatalf("mountain terrain is too dense: %d/%d", mountain, total)
	}
	if water == 0 || mountain == 0 {
		t.Fatalf("expected sparse but non-zero water and mountain terrain, got water=%d mountain=%d", water, mountain)
	}
	if ruins*10000 > total*8 {
		t.Fatalf("ruins terrain is too dense: %d/%d", ruins, total)
	}
	if ruins == 0 {
		t.Fatalf("expected very rare but non-zero ruins terrain")
	}
	if stone != 0 {
		t.Fatalf("stone terrain must not be generated: %d", stone)
	}
}

func TestTerrainPlacesSixOilWellsOnWrappedWorld(t *testing.T) {
	generator := New("test-world", 20260727, 10)
	var oilWells []world.Coord

	for y := 0; y < worldSizeTiles; y++ {
		for x := 0; x < worldSizeTiles; x++ {
			tile := generator.Tile(world.Coord{X: x, Y: y})
			if tile.Terrain == world.TerrainOilWell {
				oilWells = append(oilWells, tile.Coord)
			}
		}
	}

	if len(oilWells) != 6 {
		t.Fatalf("oil well terrain count = %d, want 6: %#v", len(oilWells), oilWells)
	}
	expected := map[world.Coord]bool{
		{X: 24, Y: 18}:   false,
		{X: 91, Y: 73}:   false,
		{X: 126, Y: 35}:  false,
		{X: 38, Y: 124}:  false,
		{X: 142, Y: 116}: false,
		{X: 76, Y: 139}:  false,
	}
	for _, coord := range oilWells {
		if _, ok := expected[coord]; !ok {
			t.Fatalf("unexpected oil well coordinate: %#v", coord)
		}
		expected[coord] = true
	}
	for coord, seen := range expected {
		if !seen {
			t.Fatalf("missing oil well coordinate: %#v", coord)
		}
	}
}
