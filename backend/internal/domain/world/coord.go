package world

import "fmt"

const ChunkSize = 32

type Coord struct {
	X int
	Y int
}

type ChunkCoord struct {
	X int
	Y int
}

type TerrainType string

const (
	TerrainGrass    TerrainType = "grass"
	TerrainForest   TerrainType = "forest"
	TerrainWater    TerrainType = "water"
	TerrainMountain TerrainType = "mountain"
	TerrainRoad     TerrainType = "road"
	TerrainOilWell  TerrainType = "oil_well"
	TerrainRuins    TerrainType = "ruins"
)

type WorldMap struct {
	ID          string
	Name        string
	Seed        int64
	ChunkSize   int
	SpawnRadius int
}

type Chunk struct {
	MapID   string
	Coord   ChunkCoord
	Version int64
	Tiles   []Tile
}

type Tile struct {
	MapID         string
	Coord         Coord
	Chunk         ChunkCoord
	Terrain       TerrainType
	Elevation     int
	SafeZone      bool
	ForestDensity int
}

type Viewport struct {
	Center Coord
	Radius int
}

func ChunkForTile(tile Coord) ChunkCoord {
	return ChunkCoord{
		X: floorDiv(tile.X, ChunkSize),
		Y: floorDiv(tile.Y, ChunkSize),
	}
}

func ChunkID(mapID string, coord ChunkCoord) string {
	return fmt.Sprintf("%s:%d:%d", mapID, coord.X, coord.Y)
}

func TileLocalCoord(tile Coord) Coord {
	chunk := ChunkForTile(tile)
	return Coord{
		X: tile.X - chunk.X*ChunkSize,
		Y: tile.Y - chunk.Y*ChunkSize,
	}
}

func ChunkOrigin(coord ChunkCoord) Coord {
	return Coord{X: coord.X * ChunkSize, Y: coord.Y * ChunkSize}
}

func TilesInChunk(coord ChunkCoord) []Coord {
	origin := ChunkOrigin(coord)
	tiles := make([]Coord, 0, ChunkSize*ChunkSize)
	for y := 0; y < ChunkSize; y++ {
		for x := 0; x < ChunkSize; x++ {
			tiles = append(tiles, Coord{X: origin.X + x, Y: origin.Y + y})
		}
	}
	return tiles
}

func ChunksAround(center ChunkCoord, radius int) []ChunkCoord {
	if radius < 0 {
		radius = 0
	}
	chunks := make([]ChunkCoord, 0, (radius*2+1)*(radius*2+1))
	for y := center.Y - radius; y <= center.Y+radius; y++ {
		for x := center.X - radius; x <= center.X+radius; x++ {
			chunks = append(chunks, ChunkCoord{X: x, Y: y})
		}
	}
	return chunks
}

func floorDiv(value int, divisor int) int {
	result := value / divisor
	if value < 0 && value%divisor != 0 {
		result--
	}
	return result
}
