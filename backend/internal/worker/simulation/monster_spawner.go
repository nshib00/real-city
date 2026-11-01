package simulation

import (
	"context"
	"fmt"
	"log/slog"
	"math"
	"sort"
	"strconv"
	"strings"
	"time"

	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"real-city/backend/internal/service/worldgen"
)

const (
	monsterSpawnPointCount = 100
	monsterSpawnSafeRange  = 3
)

type MonsterSpawner struct {
	service   *service.MonsterService
	monsters  service.MonsterRepository
	buildings service.BuildingRepository
	worlds    service.WorldRepository
	log       *slog.Logger
}

func NewMonsterSpawner(monsterService *service.MonsterService, monsters service.MonsterRepository, buildings service.BuildingRepository, worlds service.WorldRepository, log *slog.Logger) *MonsterSpawner {
	return &MonsterSpawner{service: monsterService, monsters: monsters, buildings: buildings, worlds: worlds, log: log}
}

func (s *MonsterSpawner) Tick(ctx context.Context, now time.Time, limit int) (int, error) {
	if s.service == nil || s.monsters == nil {
		return 0, nil
	}
	spawns, err := s.ensureSpawnPoints(ctx, now)
	if err != nil {
		return 0, err
	}
	aliveBySpawn, err := s.monsters.CountAliveBySpawn(ctx, service.DefaultWorldID)
	if err != nil {
		return 0, err
	}
	spawned := 0
	for _, spawn := range spawns {
		if limit > 0 && spawned >= limit {
			break
		}
		spawn = normalizeSpawnPoint(spawn, now)
		if spawn.NextSpawnAt.After(now) || aliveBySpawn[spawn.ID] >= spawn.MaxAlive {
			continue
		}
		relocated, err := s.relocateIfUnsafe(ctx, spawn, now)
		if err != nil {
			return spawned, err
		}
		spawn = relocated
		unsafe, err := s.spawnUnsafe(ctx, spawn.Tile)
		if err != nil {
			return spawned, err
		}
		if unsafe {
			continue
		}
		if _, err := s.service.SpawnFromPoint(ctx, spawn, now); err != nil {
			return spawned, err
		}
		aliveBySpawn[spawn.ID]++
		spawned++
		s.log.Info("pve.monster.spawn_point.used", "event", "pve.monster.spawn_point.used", "spawn_id", spawn.ID, "tile_x", spawn.Tile.X, "tile_y", spawn.Tile.Y)
	}
	return spawned, nil
}

func (s *MonsterSpawner) ensureSpawnPoints(ctx context.Context, now time.Time) ([]monster.SpawnPoint, error) {
	spawns, err := s.monsters.ListSpawnPoints(ctx, service.DefaultWorldID)
	if err != nil {
		return nil, err
	}
	byID := make(map[monster.SpawnID]monster.SpawnPoint, len(spawns))
	for _, spawn := range spawns {
		if _, generated := generatedSpawnIndex(spawn.ID); generated {
			byID[spawn.ID] = spawn
		}
	}
	for _, seed := range defaultSpawnSeeds(now) {
		if _, ok := byID[seed.ID]; ok {
			continue
		}
		seed, err = s.relocateIfUnsafe(ctx, seed, now)
		if err != nil {
			return nil, err
		}
		if err := s.monsters.SaveSpawnPoint(ctx, seed); err != nil {
			return nil, err
		}
		byID[seed.ID] = seed
	}
	spawns = spawns[:0]
	for _, item := range byID {
		spawns = append(spawns, normalizeSpawnPoint(item, now))
	}
	sort.Slice(spawns, func(i, j int) bool { return spawns[i].ID < spawns[j].ID })
	return spawns, nil
}

func (s *MonsterSpawner) relocateIfUnsafe(ctx context.Context, spawn monster.SpawnPoint, now time.Time) (monster.SpawnPoint, error) {
	unsafe, err := s.spawnUnsafe(ctx, spawn.Tile)
	if err != nil {
		return monster.SpawnPoint{}, err
	}
	if !unsafe {
		return spawn, nil
	}
	for ring := monsterSpawnSafeRange + 1; ring <= spawn.Radius+12; ring++ {
		for _, candidate := range ringCandidates(spawn.Tile, ring) {
			candidate = wrappedCoord(candidate)
			unsafe, err := s.spawnUnsafe(ctx, candidate)
			if err != nil {
				return monster.SpawnPoint{}, err
			}
			if unsafe {
				continue
			}
			spawn.Tile = candidate
			spawn.UpdatedAt = now
			if err := s.monsters.SaveSpawnPoint(ctx, spawn); err != nil {
				return monster.SpawnPoint{}, err
			}
			return spawn, nil
		}
	}
	return spawn, nil
}

func (s *MonsterSpawner) spawnUnsafe(ctx context.Context, tile world.Coord) (bool, error) {
	passable, err := s.tilePassable(ctx, tile)
	if err != nil || !passable {
		return true, err
	}
	if s.buildings == nil {
		return false, nil
	}
	for _, offsetX := range spawnOffsets(tile.X) {
		for _, offsetY := range spawnOffsets(tile.Y) {
			buildings, err := s.buildings.ListIntersectingFootprint(ctx, service.DefaultWorldID,
				tile.X+offsetX-monsterSpawnSafeRange, tile.Y+offsetY-monsterSpawnSafeRange,
				tile.X+offsetX+monsterSpawnSafeRange, tile.Y+offsetY+monsterSpawnSafeRange)
			if err != nil {
				return false, err
			}
			for _, item := range buildings {
				for _, occupied := range item.OccupiedTiles() {
					if wrappedChebyshev(tile, occupied) <= monsterSpawnSafeRange {
						return true, nil
					}
				}
			}
		}
	}
	return false, nil
}

func spawnOffsets(coordinate int) []int {
	offsets := []int{0}
	if coordinate < monsterSpawnSafeRange {
		offsets = append(offsets, worldgen.WorldSizeTiles)
	}
	if coordinate >= worldgen.WorldSizeTiles-monsterSpawnSafeRange {
		offsets = append(offsets, -worldgen.WorldSizeTiles)
	}
	return offsets
}

func (s *MonsterSpawner) tilePassable(ctx context.Context, tile world.Coord) (bool, error) {
	if s.worlds == nil {
		return true, nil
	}
	chunk, _, err := s.worlds.GetOrCreateChunk(ctx, service.DefaultWorldID, world.ChunkForTile(tile))
	if err != nil {
		return false, err
	}
	for _, item := range chunk.Tiles {
		if item.Coord == tile {
			return item.Terrain == world.TerrainGrass && !item.SafeZone, nil
		}
	}
	return false, nil
}

func defaultSpawnSeeds(now time.Time) []monster.SpawnPoint {
	items := make([]monster.SpawnPoint, 0, monsterSpawnPointCount)
	columns := int(math.Ceil(math.Sqrt(float64(monsterSpawnPointCount))))
	rows := (monsterSpawnPointCount + columns - 1) / columns
	for index := 0; index < monsterSpawnPointCount; index++ {
		// Spread points across the wrapped map. Stored positions can move when
		// terrain or nearby construction makes a cell unsafe.
		x, y := index%columns, index/columns
		seed := world.Coord{
			X: (2*x + 1) * worldgen.WorldSizeTiles / (2 * columns),
			Y: (2*y + 1) * worldgen.WorldSizeTiles / (2 * rows),
		}
		items = append(items, monster.SpawnPoint{
			ID:          monster.SpawnID(fmt.Sprintf("spawn_generated_%03d", index)),
			MapID:       service.DefaultWorldID,
			Type:        monster.TypeRoamingMelee,
			Tile:        seed,
			Radius:      8,
			MaxAlive:    1,
			Cooldown:    90 * time.Second,
			NextSpawnAt: now.Add(time.Duration(index+1) * time.Second),
			CreatedAt:   now,
			UpdatedAt:   now,
		})
	}
	return items
}

func generatedSpawnIndex(id monster.SpawnID) (int, bool) {
	part, ok := strings.CutPrefix(string(id), "spawn_generated_")
	if !ok || len(part) != 3 {
		return 0, false
	}
	index, err := strconv.Atoi(part)
	return index, err == nil && index >= 0 && index < monsterSpawnPointCount
}

func wrappedCoord(tile world.Coord) world.Coord { return world.NormalizeCoord(tile) }

func wrappedChebyshev(a, b world.Coord) int {
	a, b = wrappedCoord(a), wrappedCoord(b)
	dx, dy := absInt(a.X-b.X), absInt(a.Y-b.Y)
	size := worldgen.WorldSizeTiles
	return max(min(dx, size-dx), min(dy, size-dy))
}

func absInt(value int) int {
	if value < 0 {
		return -value
	}
	return value
}

func normalizeSpawnPoint(spawn monster.SpawnPoint, now time.Time) monster.SpawnPoint {
	if spawn.Radius <= 0 {
		spawn.Radius = 8
	}
	if spawn.MaxAlive <= 0 || spawn.MaxAlive > 1 {
		spawn.MaxAlive = 1
	}
	if spawn.Cooldown <= 0 || spawn.Cooldown > 2*time.Minute {
		spawn.Cooldown = 90 * time.Second
	}
	if spawn.NextSpawnAt.IsZero() {
		spawn.NextSpawnAt = now.Add(service.RandomSpawnCooldown())
	}
	if spawn.CreatedAt.IsZero() {
		spawn.CreatedAt = now
	}
	if spawn.UpdatedAt.IsZero() {
		spawn.UpdatedAt = now
	}
	return spawn
}

func ringCandidates(center world.Coord, radius int) []world.Coord {
	items := make([]world.Coord, 0, radius*8)
	for dx := -radius; dx <= radius; dx++ {
		items = append(items, world.Coord{X: center.X + dx, Y: center.Y - radius})
		items = append(items, world.Coord{X: center.X + dx, Y: center.Y + radius})
	}
	for dy := -radius + 1; dy <= radius-1; dy++ {
		items = append(items, world.Coord{X: center.X - radius, Y: center.Y + dy})
		items = append(items, world.Coord{X: center.X + radius, Y: center.Y + dy})
	}
	return items
}
