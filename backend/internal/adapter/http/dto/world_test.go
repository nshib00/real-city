package dto

import (
	"testing"

	"real-city/backend/internal/domain/world"
)

func TestTileIncludesRuinType(t *testing.T) {
	response := Tile(world.Tile{Terrain: world.TerrainRuins, RuinType: "ruins_archive"})
	if response.Terrain != "ruins" || response.RuinType != "ruins_archive" {
		t.Fatalf("unexpected ruin tile response: %#v", response)
	}
}
