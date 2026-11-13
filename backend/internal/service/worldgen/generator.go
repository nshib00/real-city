package worldgen

import (
	"hash/fnv"
	"math"
	"math/rand"
	"sort"

	"real-city/backend/internal/domain/world"
)

const WorldSizeTiles = world.WorldSize

const oilWellCount = 6

var ruinTypes = [...]string{
	"ruins_town_square",
	"ruins_archive",
	"ruins_mint",
	"ruins_storage",
	"ruins_greenhouse",
	"ruins_water_station",
	"ruins_bastion",
	"ruins_mechanic_workshop",
	"ruins_wind_shrine",
	"ruins_ore_obelisk",
	"ruins_rift_watch",
	"ruins_river_lighthouse",
}

type Generator struct {
	mapID       string
	seed        int64
	spawnRadius int
	oilWells    map[world.Coord]struct{}
}

func New(mapID string, seed int64, spawnRadius int) Generator {
	generator := Generator{mapID: mapID, seed: seed, spawnRadius: spawnRadius}
	generator.oilWells = generator.pickOilWells(oilWellCount)
	return generator
}

func (g Generator) OilWellTiles() []world.Coord {
	coords := make([]world.Coord, 0, len(g.oilWells))
	for coord := range g.oilWells {
		coords = append(coords, coord)
	}
	sort.Slice(coords, func(i, j int) bool {
		if coords[i].Y != coords[j].Y {
			return coords[i].Y < coords[j].Y
		}
		return coords[i].X < coords[j].X
	})
	return coords
}

func (g Generator) pickOilWells(count int) map[world.Coord]struct{} {
	tiles := make(map[world.Coord]struct{}, count)
	rng := rand.New(rand.NewSource(g.seed))
	for attempt := 0; attempt < count*128 && len(tiles) < count; attempt++ {
		coord := world.Coord{
			X: rng.Intn(WorldSizeTiles),
			Y: rng.Intn(WorldSizeTiles),
		}
		if g.canHostOilWell(coord) {
			tiles[coord] = struct{}{}
		}
	}
	if len(tiles) < count {
		for y := 0; y < WorldSizeTiles && len(tiles) < count; y++ {
			for x := 0; x < WorldSizeTiles && len(tiles) < count; x++ {
				coord := world.Coord{X: x, Y: y}
				if g.canHostOilWell(coord) {
					tiles[coord] = struct{}{}
				}
			}
		}
	}
	return tiles
}

func (g Generator) canHostOilWell(coord world.Coord) bool {
	distance := math.Hypot(float64(coord.X), float64(coord.Y))
	if distance <= float64(g.spawnRadius) {
		return false
	}
	return g.terrain(coord, distance, false) == world.TerrainGrass
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
	coord = world.NormalizeChunk(coord)
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
	ruinType := ""
	if terrain == world.TerrainRuins {
		ruinType = ruinTypes[g.noiseModulo(coord, 271, uint32(len(ruinTypes)))]
	}
	return world.Tile{
		MapID:         g.mapID,
		Coord:         coord,
		Chunk:         chunk,
		Terrain:       terrain,
		RuinType:      ruinType,
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
	ruins := g.noiseModulo(coord, 131, 10000)
	switch {
	case !safeZone && distance > 32 && ruins < 3:
		return world.TerrainRuins
	case !safeZone && g.isOilWellTile(coord):
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

func (g Generator) isOilWellTile(coord world.Coord) bool {
	wrapped := world.Coord{X: positiveModulo(coord.X, WorldSizeTiles), Y: positiveModulo(coord.Y, WorldSizeTiles)}
	_, ok := g.oilWells[wrapped]
	return ok
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

func positiveModulo(value int, size int) int {
	result := value % size
	if result < 0 {
		result += size
	}
	return result
}
