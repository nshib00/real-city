package worldgen

import (
	"testing"

	"real-city/backend/internal/domain/world"
)

func TestTerrainKeepsRiversAndMountainsSparse(t *testing.T) {
	generator := New("test-world", 20260727, 10)
	var water int
	var mountain int
	var oilWell int
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
			case world.TerrainOilWell:
				oilWell++
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
	if oilWell*1000 > total*6 {
		t.Fatalf("oil well terrain is too dense: %d/%d", oilWell, total)
	}
	if oilWell == 0 {
		t.Fatalf("expected very sparse but non-zero oil well terrain")
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
