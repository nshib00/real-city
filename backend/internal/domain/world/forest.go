package world

const MaxForestDensity = 3

func (t Tile) CanChopForest() bool {
	return t.Terrain == TerrainForest && t.ForestDensity > 0
}

func ChopForest(tile Tile) (Tile, bool) {
	if !tile.CanChopForest() {
		return tile, false
	}
	tile.ForestDensity--
	if tile.ForestDensity <= 0 {
		tile.ForestDensity = 0
		tile.Terrain = TerrainGrass
	}
	return tile, true
}
