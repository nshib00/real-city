package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type MonsterRepo struct {
	mu     sync.RWMutex
	items  map[monster.ID]monster.Monster
	spawns map[monster.SpawnID]monster.SpawnPoint
	events []monster.Event
}

func NewMonsterRepo() *MonsterRepo {
	now := time.Now().UTC()
	items := make(map[monster.ID]monster.Monster)
	for _, seed := range []struct {
		id   monster.ID
		kind monster.Type
		tile world.Coord
	}{
		{"monster_roamer_1", monster.TypeRoamingMelee, world.Coord{X: 10, Y: -3}},
		{"monster_resource_1", monster.TypeResourceGuardian, world.Coord{X: 14, Y: 6}},
		{"monster_ruins_1", monster.TypeRuinsGuardian, world.Coord{X: -8, Y: 12}},
	} {
		spec, _ := catalog.MonsterSpec(seed.kind)
		items[seed.id] = fromSpec(seed.id, "dev-world", seed.tile, spec, now)
	}
	return &MonsterRepo{
		items: items,
		spawns: map[monster.SpawnID]monster.SpawnPoint{
			"spawn_roamers": {ID: "spawn_roamers", MapID: "dev-world", Type: monster.TypeRoamingMelee, Tile: world.Coord{X: 6, Y: -7}, Radius: 8, MaxAlive: 4, Cooldown: 10 * time.Minute, NextSpawnAt: now.Add(2 * time.Minute), CreatedAt: now, UpdatedAt: now},
			"spawn_ruins":   {ID: "spawn_ruins", MapID: "dev-world", Type: monster.TypeRuinsGuardian, Tile: world.Coord{X: -8, Y: 12}, Radius: 4, MaxAlive: 2, Cooldown: 18 * time.Minute, NextSpawnAt: now.Add(4 * time.Minute), CreatedAt: now, UpdatedAt: now},
		},
	}
}

func (r *MonsterRepo) Create(ctx context.Context, item monster.Monster) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.items[item.ID] = item
	return nil
}

func (r *MonsterRepo) FindByID(ctx context.Context, id monster.ID) (monster.Monster, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	item, ok := r.items[id]
	if !ok {
		return monster.Monster{}, apperror.New(apperror.NotFound, "monster not found")
	}
	return item, nil
}

func (r *MonsterRepo) ListByMap(ctx context.Context, mapID string) ([]monster.Monster, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]monster.Monster, 0, len(r.items))
	for _, item := range r.items {
		if item.MapID == mapID && item.State != monster.StateDead {
			items = append(items, item)
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
	return items, nil
}

func (r *MonsterRepo) ListByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]monster.Monster, error) {
	items, err := r.ListByMap(ctx, mapID)
	if err != nil {
		return nil, err
	}
	filtered := make([]monster.Monster, 0, len(items))
	for _, item := range items {
		if item.Tile.X >= minX && item.Tile.X <= maxX && item.Tile.Y >= minY && item.Tile.Y <= maxY {
			filtered = append(filtered, item)
		}
	}
	return filtered, nil
}

func (r *MonsterRepo) Update(ctx context.Context, item monster.Monster) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.items[item.ID] = item
	return nil
}

func (r *MonsterRepo) ListSpawnPoints(ctx context.Context, mapID string) ([]monster.SpawnPoint, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]monster.SpawnPoint, 0, len(r.spawns))
	for _, item := range r.spawns {
		if item.MapID == mapID {
			items = append(items, item)
		}
	}
	return items, nil
}

func (r *MonsterRepo) SaveSpawnPoint(ctx context.Context, item monster.SpawnPoint) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.spawns[item.ID] = item
	return nil
}

func (r *MonsterRepo) AddEvent(ctx context.Context, item monster.Event) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.events = append(r.events, item)
	return nil
}

func fromSpec(id monster.ID, mapID string, tile world.Coord, spec monster.Spec, now time.Time) monster.Monster {
	return monster.Monster{
		ID: id, MapID: mapID, Type: spec.Type, State: monster.StateWandering, Tile: tile, HomeTile: tile,
		Health: spec.MaxHealth, MaxHealth: spec.MaxHealth, Damage: spec.Damage, SpeedTiles: spec.SpeedTiles,
		AggroRadius: spec.AggroRadius, AttackRange: spec.AttackRange, AttackCooldown: spec.AttackCooldown,
		LastMovedAt: now, LootCoins: spec.LootCoins, CreatedAt: now, UpdatedAt: now,
	}
}
