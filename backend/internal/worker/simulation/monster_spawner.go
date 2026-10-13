package simulation

import (
	"context"
	"log/slog"
	"math/rand"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

const (
	monsterSpawnPointCount = 10
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
		relocated, err := s.relocateIfUnsafe(ctx, spawn, now)
		if err != nil {
			return spawned, err
		}
		spawn = relocated
		if spawn.NextSpawnAt.After(now) || aliveBySpawn[spawn.ID] >= spawn.MaxAlive {
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
		byID[spawn.ID] = spawn
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
	for ring := monsterSpawnSafeRange; ring <= spawn.Radius+12; ring++ {
		for _, candidate := range ringCandidates(spawn.Tile, ring) {
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
	buildings, err := s.buildings.ListByViewport(
		ctx,
		service.DefaultWorldID,
		tile.X-monsterSpawnSafeRange,
		tile.Y-monsterSpawnSafeRange,
		tile.X+monsterSpawnSafeRange,
		tile.Y+monsterSpawnSafeRange,
	)
	if err != nil {
		return false, err
	}
	for _, item := range buildings {
		if item.State == building.StateRuined {
			continue
		}
		for _, occupied := range item.OccupiedTiles() {
			if manhattan(tile, occupied) < monsterSpawnSafeRange {
				return true, nil
			}
		}
	}
	return false, nil
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
			return item.Terrain == world.TerrainForest || item.Terrain == world.TerrainGrass, nil
		}
	}
	return false, nil
}

func defaultSpawnSeeds(now time.Time) []monster.SpawnPoint {
	specs := catalog.MonsterSpecs()
	defaultType := monster.TypeRoamingMelee
	if len(specs) > 0 {
		defaultType = specs[rand.Intn(len(specs))].Type
	}
	coords := []struct {
		id   monster.SpawnID
		tile world.Coord
	}{
		{"spawn_roamers", world.Coord{X: 6, Y: -7}},
		{"spawn_resources", world.Coord{X: 14, Y: 6}},
		{"spawn_ruins", world.Coord{X: -8, Y: 12}},
		{"spawn_north_forest", world.Coord{X: -16, Y: -18}},
		{"spawn_east_grove", world.Coord{X: 24, Y: -9}},
		{"spawn_south_meadow", world.Coord{X: 8, Y: 22}},
		{"spawn_west_ruins", world.Coord{X: -24, Y: 8}},
		{"spawn_far_north", world.Coord{X: 3, Y: -29}},
		{"spawn_far_east", world.Coord{X: 31, Y: 13}},
		{"spawn_far_south", world.Coord{X: -11, Y: 30}},
	}
	items := make([]monster.SpawnPoint, 0, monsterSpawnPointCount)
	for i, seed := range coords {
		items = append(items, monster.SpawnPoint{
			ID:          seed.id,
			MapID:       service.DefaultWorldID,
			Type:        defaultType,
			Tile:        seed.tile,
			Radius:      8,
			MaxAlive:    1,
			Cooldown:    90 * time.Second,
			NextSpawnAt: now.Add(time.Duration(i+1) * 10 * time.Second),
			CreatedAt:   now,
			UpdatedAt:   now,
		})
	}
	return items
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
