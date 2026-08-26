package worldgen

import (
	"hash/fnv"
	"math"

	"real-city/backend/internal/domain/world"
)

type Generator struct {
	mapID       string
	seed        int64
	spawnRadius int
}

func New(mapID string, seed int64, spawnRadius int) Generator {
	return Generator{mapID: mapID, seed: seed, spawnRadius: spawnRadius}
}

func (g Generator) Map() world.WorldMap {
	return world.WorldMap{
		ID:          g.mapID,
		Name:        "Frontier Basin",
		Seed:        g.seed,
		ChunkSize:   world.ChunkSize,
		SpawnRadius: g.spawnRadius,
	}
}

func (g Generator) Chunk(coord world.ChunkCoord) world.Chunk {
	tiles := world.TilesInChunk(coord)
	chunk := world.Chunk{
		MapID:   g.mapID,
		Coord:   coord,
		Version: g.version(coord),
		Tiles:   make([]world.Tile, 0, len(tiles)),
	}
	for _, tileCoord := range tiles {
		chunk.Tiles = append(chunk.Tiles, g.Tile(tileCoord))
	}
	return chunk
}

func (g Generator) Tile(coord world.Coord) world.Tile {
	chunk := world.ChunkForTile(coord)
	distance := math.Hypot(float64(coord.X), float64(coord.Y))
	safeZone := distance <= float64(g.spawnRadius)
	terrain := g.terrain(coord, distance, safeZone)
	forestDensity := 0
	if terrain == world.TerrainForest {
		forestDensity = world.MaxForestDensity
	}
	return world.Tile{
		MapID:         g.mapID,
		Coord:         coord,
		Chunk:         chunk,
		Terrain:       terrain,
		Elevation:     g.elevation(coord),
		SafeZone:      safeZone,
		ForestDensity: forestDensity,
	}
}

func (g Generator) terrain(coord world.Coord, distance float64, safeZone bool) world.TerrainType {
	if safeZone && math.Abs(float64(coord.X)) <= 2 && math.Abs(float64(coord.Y)) <= 2 {
		return world.TerrainGrass
	}
	value := g.noise(coord, 0)
	ridge := g.noise(coord, 17)
	oil := g.noise(coord, 89)
	ruins := g.noiseModulo(coord, 131, 10000)
	switch {
	case !safeZone && distance > 32 && ruins < 3:
		return world.TerrainRuins
	case !safeZone && distance > 20 && oil == 0 && ridge < 35:
		return world.TerrainOilWell
	case !safeZone && value < 2:
		return world.TerrainWater
	case ridge > 97 && distance > 18:
		return world.TerrainMountain
	case value > 76:
		return world.TerrainForest
	default:
		return world.TerrainGrass
	}
}

func (g Generator) elevation(coord world.Coord) int {
	return int(g.noise(coord, 41)%4) - 1
}

func (g Generator) version(coord world.ChunkCoord) int64 {
	return int64(g.noise(world.Coord{X: coord.X, Y: coord.Y}, 73)) + 1
}

func (g Generator) noise(coord world.Coord, salt int64) uint32 {
	return g.noiseModulo(coord, salt, 100)
}

func (g Generator) noiseModulo(coord world.Coord, salt int64, modulo uint32) uint32 {
	h := fnv.New32a()
	_, _ = h.Write([]byte{
		byte(g.seed), byte(g.seed >> 8), byte(g.seed >> 16), byte(g.seed >> 24),
		byte(coord.X), byte(coord.X >> 8), byte(coord.X >> 16), byte(coord.X >> 24),
		byte(coord.Y), byte(coord.Y >> 8), byte(coord.Y >> 16), byte(coord.Y >> 24),
		byte(salt), byte(salt >> 8),
	})
	return h.Sum32() % modulo
}
