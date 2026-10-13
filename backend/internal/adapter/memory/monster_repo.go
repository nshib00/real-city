package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type MonsterRepo struct {
	mu     sync.RWMutex
	items  map[monster.ID]monster.Monster
	spawns map[monster.SpawnID]monster.SpawnPoint
	loot   map[monster.LootDropID]monster.LootDrop
	events []monster.Event
}

func NewMonsterRepo() *MonsterRepo {
	now := time.Now().UTC()
	items := make(map[monster.ID]monster.Monster)
	for _, seed := range []struct {
		id      monster.ID
		spawnID monster.SpawnID
		kind    monster.Type
		tile    world.Coord
	}{
		{"monster_roamer_1", "spawn_roamers", monster.TypeRoamingMelee, world.Coord{X: 10, Y: -3}},
		{"monster_resource_1", "spawn_resources", monster.TypeResourceGuardian, world.Coord{X: 14, Y: 6}},
		{"monster_ruins_1", "spawn_ruins", monster.TypeRuinsGuardian, world.Coord{X: -8, Y: 12}},
	} {
		spec, _ := catalog.MonsterSpec(seed.kind)
		item := fromSpec(seed.id, "dev-world", seed.tile, spec, now)
		item.SpawnID = seed.spawnID
		items[seed.id] = item
	}
	return &MonsterRepo{
		items: items,
		spawns: map[monster.SpawnID]monster.SpawnPoint{
			"spawn_roamers": {ID: "spawn_roamers", MapID: "dev-world", Type: monster.TypeRoamingMelee, Tile: world.Coord{X: 6, Y: -7}, Radius: 8, MaxAlive: 4, Cooldown: 10 * time.Minute, NextSpawnAt: now.Add(2 * time.Minute), CreatedAt: now, UpdatedAt: now},
			"spawn_ruins":   {ID: "spawn_ruins", MapID: "dev-world", Type: monster.TypeRuinsGuardian, Tile: world.Coord{X: -8, Y: 12}, Radius: 4, MaxAlive: 2, Cooldown: 18 * time.Minute, NextSpawnAt: now.Add(4 * time.Minute), CreatedAt: now, UpdatedAt: now},
		},
		loot: map[monster.LootDropID]monster.LootDrop{},
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

func (r *MonsterRepo) ListActiveForTick(ctx context.Context, mapID string, limit int) ([]monster.Monster, error) {
	items, err := r.ListByMap(ctx, mapID)
	if err != nil {
		return nil, err
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].UpdatedAt.Equal(items[j].UpdatedAt) {
			return items[i].ID < items[j].ID
		}
		return items[i].UpdatedAt.Before(items[j].UpdatedAt)
	})
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
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

func (r *MonsterRepo) CountAliveBySpawn(ctx context.Context, mapID string) (map[monster.SpawnID]int, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	counts := make(map[monster.SpawnID]int)
	for _, item := range r.items {
		if item.MapID == mapID && item.SpawnID != "" && item.Alive() {
			counts[item.SpawnID]++
		}
	}
	return counts, nil
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

func (r *MonsterRepo) CreateLootDrop(ctx context.Context, item monster.LootDrop) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.loot[item.ID]; ok {
		return apperror.New(apperror.Conflict, "loot drop already exists")
	}
	r.loot[item.ID] = cloneLootDrop(item)
	return nil
}

func (r *MonsterRepo) FindLootDrop(ctx context.Context, id monster.LootDropID) (monster.LootDrop, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	item, ok := r.loot[id]
	if !ok {
		return monster.LootDrop{}, apperror.New(apperror.NotFound, "loot drop not found")
	}
	return cloneLootDrop(item), nil
}

func (r *MonsterRepo) ListLootDropsByViewport(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]monster.LootDrop, error) {
	_ = ctx
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]monster.LootDrop, 0, len(r.loot))
	for _, item := range r.loot {
		if item.MapID == mapID && item.ClaimedBy == "" && item.Tile.X >= minX && item.Tile.X <= maxX && item.Tile.Y >= minY && item.Tile.Y <= maxY {
			items = append(items, cloneLootDrop(item))
		}
	}
	sort.Slice(items, func(i, j int) bool { return items[i].CreatedAt.Before(items[j].CreatedAt) })
	return items, nil
}

func (r *MonsterRepo) ClaimLootDrop(ctx context.Context, id monster.LootDropID, playerID player.ID, now time.Time) (monster.LootDrop, error) {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	item, ok := r.loot[id]
	if !ok {
		return monster.LootDrop{}, apperror.New(apperror.NotFound, "loot drop not found")
	}
	if item.ClaimedBy != "" {
		return monster.LootDrop{}, apperror.New(apperror.Conflict, "loot drop is already claimed")
	}
	item.ClaimedBy = string(playerID)
	item.ClaimedAt = &now
	r.loot[id] = item
	return cloneLootDrop(item), nil
}

func (r *MonsterRepo) AddEvent(ctx context.Context, item monster.Event) error {
	_ = ctx
	r.mu.Lock()
	defer r.mu.Unlock()
	r.events = append(r.events, item)
	return nil
}

func cloneLootDrop(item monster.LootDrop) monster.LootDrop {
	item.Items = append([]economy.ResourceAmount(nil), item.Items...)
	return item
}

func fromSpec(id monster.ID, mapID string, tile world.Coord, spec monster.Spec, now time.Time) monster.Monster {
	return monster.Monster{
		ID: id, MapID: mapID, Type: spec.Type, State: monster.StateWandering, Tile: tile, HomeTile: tile,
		Health: spec.MaxHealth, MaxHealth: spec.MaxHealth, Damage: spec.Damage, SpeedTiles: spec.SpeedTiles,
		AggroRadius: spec.AggroRadius, AttackRange: spec.AttackRange, AttackCooldown: spec.AttackCooldown,
		LastMovedAt: now, LootCoins: spec.LootCoins, CreatedAt: now, UpdatedAt: now,
	}
}
