package building

import (
	"fmt"

	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type PlacementInput struct {
	Type             Type
	Tile             world.Tile
	Tiles            []world.Tile
	Footprint        Footprint
	Existing         []Building
	HasTownHall      bool
	BuildingLimit    int
	UsedLimit        int
	RequiresTownHall bool
}

func ValidatePlacement(input PlacementInput) error {
	if input.Footprint.Width <= 0 || input.Footprint.Height <= 0 {
		return apperror.WithFields(apperror.Validation, "building footprint must be positive", map[string]string{"footprint": "must be positive"})
	}
	if input.Type != TypeTownHall && input.RequiresTownHall && !input.HasTownHall {
		return apperror.New(apperror.Conflict, "town hall is required before other buildings")
	}
	if input.Type == TypeTownHall && input.HasTownHall {
		return apperror.New(apperror.Conflict, "town hall already exists")
	}
	if input.Type != TypeRoad && input.UsedLimit >= input.BuildingLimit {
		return apperror.New(apperror.Conflict, "building limit reached")
	}
	terrainTiles := terrainTilesByCoord(input.Tile, input.Tiles)
	for _, coord := range footprintTiles(input.Tile.Coord, input.Footprint) {
		tile, ok := terrainTiles[coord]
		if !ok {
			continue
		}
		if tile.Terrain == world.TerrainWater || tile.Terrain == world.TerrainMountain || tile.Terrain == world.TerrainForest {
			return apperror.WithFields(apperror.Validation, "terrain does not allow building placement", map[string]string{"terrain": string(tile.Terrain), "tile": coordKey(coord)})
		}
		if input.Type != TypeRoad && tile.Terrain == world.TerrainOilWell {
			return apperror.WithFields(apperror.Validation, "oil wells must be claimed by resource mechanics", map[string]string{"terrain": string(tile.Terrain), "tile": coordKey(coord)})
		}
	}

	occupied := occupiedTiles(input.Existing)
	for _, tile := range footprintTiles(input.Tile.Coord, input.Footprint) {
		if occupied[tile] {
			return apperror.WithFields(apperror.Conflict, "tile is occupied", map[string]string{"tile": coordKey(tile)})
		}
	}
	return nil
}

func terrainTilesByCoord(origin world.Tile, tiles []world.Tile) map[world.Coord]world.Tile {
	result := map[world.Coord]world.Tile{origin.Coord: origin}
	for _, tile := range tiles {
		result[tile.Coord] = tile
	}
	return result
}

func UsedBuildingLimit(buildings []Building) int {
	used := 0
	for _, b := range buildings {
		if !b.IsRoad() && b.State != StateRuined {
			used++
		}
	}
	return used
}

func HasTownHall(buildings []Building) bool {
	for _, b := range buildings {
		if b.Type == TypeTownHall && b.State != StateRuined {
			return true
		}
	}
	return false
}

func footprintTiles(origin world.Coord, footprint Footprint) []world.Coord {
	tiles := make([]world.Coord, 0, footprint.Width*footprint.Height)
	for y := 0; y < footprint.Height; y++ {
		for x := 0; x < footprint.Width; x++ {
			tiles = append(tiles, world.Coord{X: origin.X + x, Y: origin.Y + y})
		}
	}
	return tiles
}

func occupiedTiles(buildings []Building) map[world.Coord]bool {
	result := make(map[world.Coord]bool)
	for _, b := range buildings {
		if b.State == StateRuined {
			continue
		}
		for _, tile := range b.OccupiedTiles() {
			result[tile] = true
		}
	}
	return result
}

func coordKey(coord world.Coord) string {
	return fmt.Sprintf("%d:%d", coord.X, coord.Y)
}
