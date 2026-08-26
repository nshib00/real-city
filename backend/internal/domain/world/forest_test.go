package world

import "testing"

func TestChopForestReducesDensityAndClearsTile(t *testing.T) {
	tile := Tile{Terrain: TerrainForest, ForestDensity: MaxForestDensity}

	for expected := 2; expected >= 1; expected-- {
		var ok bool
		tile, ok = ChopForest(tile)
		if !ok {
			t.Fatal("expected forest chop to succeed")
		}
		if tile.Terrain != TerrainForest || tile.ForestDensity != expected {
			t.Fatalf("expected forest density %d, got terrain=%s density=%d", expected, tile.Terrain, tile.ForestDensity)
		}
	}

	tile, ok := ChopForest(tile)
	if !ok {
		t.Fatal("expected final forest chop to succeed")
	}
	if tile.Terrain != TerrainGrass || tile.ForestDensity != 0 {
		t.Fatalf("expected cleared grass tile, got terrain=%s density=%d", tile.Terrain, tile.ForestDensity)
	}
}

func TestChopForestRejectsNonForest(t *testing.T) {
	_, ok := ChopForest(Tile{Terrain: TerrainGrass})
	if ok {
		t.Fatal("expected non-forest tile to reject chopping")
	}
}
