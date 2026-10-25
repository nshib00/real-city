package worldgen

import (
	"testing"

	"real-city/backend/internal/domain/world"
)

func TestRuinsReceiveStableVariedTypes(t *testing.T) {
	generator := New("test-world", 20260727, 10)
	variants := make(map[string]bool)
	for y := -192; y < 192; y++ {
		for x := -192; x < 192; x++ {
			coord := world.Coord{X: x, Y: y}
			tile := generator.Tile(coord)
			if tile.Terrain != world.TerrainRuins {
				if tile.RuinType != "" {
					t.Fatalf("non-ruin tile has type %q at %+v", tile.RuinType, coord)
				}
				continue
			}
			if tile.RuinType == "" || generator.Tile(coord).RuinType != tile.RuinType {
				t.Fatalf("ruin type is missing or unstable at %+v", coord)
			}
			variants[tile.RuinType] = true
		}
	}
	if len(variants) < 4 {
		t.Fatalf("expected varied ruin types, got %#v", variants)
	}
	for variant := range variants {
		known := false
		for _, candidate := range ruinTypes {
			if variant == candidate {
				known = true
				break
			}
		}
		if !known {
			t.Fatalf("unknown ruin type %q", variant)
		}
	}
}
