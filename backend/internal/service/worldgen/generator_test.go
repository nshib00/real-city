package worldgen

import (
	"slices"
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

func TestTerrainPlacesSixRandomOilWellsOnWrappedWorld(t *testing.T) {
	generator := New("test-world", 20260727, 10)
	oilWells := oilWellCoords(generator)

	if len(oilWells) != oilWellCount {
		t.Fatalf("oil well terrain count = %d, want %d: %#v", len(oilWells), oilWellCount, oilWells)
	}
	seen := make(map[world.Coord]bool, len(oilWells))
	for _, coord := range oilWells {
		if seen[coord] {
			t.Fatalf("duplicate oil well coordinate: %#v", coord)
		}
		seen[coord] = true
		if coord.X < 0 || coord.X >= WorldSizeTiles || coord.Y < 0 || coord.Y >= WorldSizeTiles {
			t.Fatalf("oil well coordinate outside wrapped world: %#v", coord)
		}
		tile := generator.Tile(coord)
		if tile.SafeZone {
			t.Fatalf("oil well placed inside safe zone: %#v", coord)
		}
		if tile.Terrain != world.TerrainOilWell {
			t.Fatalf("tile at %#v has terrain %q, want %q", coord, tile.Terrain, world.TerrainOilWell)
		}
	}

	repeated := oilWellCoords(New("test-world", 20260727, 10))
	if !slices.Equal(oilWells, repeated) {
		t.Fatalf("oil well placement is not stable for the same seed: %#v != %#v", oilWells, repeated)
	}

	other := oilWellCoords(New("test-world", 20260728, 10))
	if slices.Equal(oilWells, other) {
		t.Fatalf("different seeds produced identical oil well placement: %#v", oilWells)
	}
}

func oilWellCoords(generator Generator) []world.Coord {
	var coords []world.Coord
	for y := 0; y < WorldSizeTiles; y++ {
		for x := 0; x < WorldSizeTiles; x++ {
			tile := generator.Tile(world.Coord{X: x, Y: y})
			if tile.Terrain == world.TerrainOilWell {
				coords = append(coords, tile.Coord)
			}
		}
	}
	return coords
}
