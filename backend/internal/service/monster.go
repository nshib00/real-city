package service

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"
	"time"

	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type MonsterService struct {
	repo    MonsterRepository
	log     *slog.Logger
	events  *EventBus
	economy *EconomyService
	now     func() time.Time
}

func NewMonsterService(repo MonsterRepository, log *slog.Logger) *MonsterService {
	return &MonsterService{repo: repo, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *MonsterService) SetEventBus(events *EventBus) {
	s.events = events
}

func (s *MonsterService) SetEconomy(economyService *EconomyService) {
	s.economy = economyService
}

func (s *MonsterService) Catalog(ctx context.Context) ([]monster.Spec, error) {
	_ = ctx
	return catalog.MonsterSpecs(), nil
}

func (s *MonsterService) List(ctx context.Context, center world.Coord, radius int) ([]monster.Monster, error) {
	if radius <= 0 {
		radius = 24
	}
	return s.repo.ListByViewport(ctx, DefaultWorldID, center.X-radius, center.Y-radius, center.X+radius, center.Y+radius)
}

func (s *MonsterService) Get(ctx context.Context, id monster.ID) (monster.Monster, error) {
	return s.repo.FindByID(ctx, id)
}

func (s *MonsterService) Attack(ctx context.Context, id monster.ID, playerID player.ID) (monster.Monster, []Reward, error) {
	item, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return monster.Monster{}, nil, err
	}
	if !item.Alive() {
		return monster.Monster{}, nil, apperror.New(apperror.Conflict, "monster is already dead")
	}
	now := s.now()
	damage := 28
	killed := item.ApplyDamage(damage, now)
	if err := s.repo.Update(ctx, item); err != nil {
		return monster.Monster{}, nil, err
	}
	rewards := []Reward(nil)
	if killed {
		if err := s.createLootDrop(ctx, item, now); err != nil {
			return monster.Monster{}, nil, err
		}
		if err := s.scheduleSpawnAfterDeath(ctx, item, now); err != nil {
			return monster.Monster{}, nil, err
		}
	}
	eventType := EventMonsterDamaged
	if killed {
		eventType = EventMonsterDied
	}
	s.publish(eventType, item, playerID)
	_ = s.repo.AddEvent(ctx, monster.Event{ID: fmt.Sprintf("monster_event_%s_%d", item.ID, now.UnixNano()), MonsterID: item.ID, Type: string(eventType), TargetID: string(playerID), Tile: item.Tile, CreatedAt: now})
	s.log.Info("pve.monster.damaged", "event", "pve.monster.damaged", "monster_id", item.ID, "monster_type", item.Type, "player_id", playerID, "damage", damage, "dead", killed, "chunk_id", world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)))
	return item, rewards, nil
}

func (s *MonsterService) SpawnFromPoint(ctx context.Context, spawn monster.SpawnPoint, now time.Time) (monster.Monster, error) {
	spec, ok := randomMonsterSpec()
	if !ok {
		return monster.Monster{}, apperror.New(apperror.Validation, "monster catalog is empty")
	}
	spawn.Type = spec.Type
	spawn.NextSpawnAt = now.Add(RandomSpawnCooldown())
	spawn.UpdatedAt = now
	if err := s.repo.SaveSpawnPoint(ctx, spawn); err != nil {
		return monster.Monster{}, err
	}
	item := monster.Monster{
		ID: monster.ID(fmt.Sprintf("monster_%s_%d", spawn.ID, now.UnixNano())), MapID: spawn.MapID, SpawnID: spawn.ID, Type: spec.Type, State: monster.StateWandering,
		Tile: spawn.Tile, HomeTile: spawn.Tile, Health: spec.MaxHealth, MaxHealth: spec.MaxHealth, Damage: spec.Damage,
		SpeedTiles: spec.SpeedTiles, AggroRadius: spec.AggroRadius, AttackRange: spec.AttackRange, AttackCooldown: spec.AttackCooldown,
		LastMovedAt: now, LootCoins: spec.LootCoins, CreatedAt: now, UpdatedAt: now,
	}
	if err := s.repo.Create(ctx, item); err != nil {
		return monster.Monster{}, err
	}
	s.publish(EventMonsterSpawned, item, "")
	s.log.Info("pve.monster.spawned", "event", "pve.monster.spawned", "monster_id", item.ID, "monster_type", item.Type, "chunk_id", world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)))
	return item, nil
}

func (s *MonsterService) ListLoot(ctx context.Context, center world.Coord, radius int) ([]monster.LootDrop, error) {
	if radius <= 0 {
		radius = 24
	}
	return s.repo.ListLootDropsByViewport(ctx, DefaultWorldID, center.X-radius, center.Y-radius, center.X+radius, center.Y+radius)
}

func (s *MonsterService) ClaimLoot(ctx context.Context, id monster.LootDropID, playerID player.ID) (monster.LootDrop, economy.Inventory, error) {
	if s.economy == nil {
		return monster.LootDrop{}, economy.Inventory{}, apperror.New(apperror.Conflict, "economy service is unavailable")
	}
	now := s.now()
	drop, err := s.repo.ClaimLootDrop(ctx, id, playerID, now)
	if err != nil {
		return monster.LootDrop{}, economy.Inventory{}, err
	}
	inventory, _, err := s.economy.Add(ctx, playerID, drop.Items, "monster:loot:"+string(drop.ID))
	if err != nil {
		return monster.LootDrop{}, economy.Inventory{}, err
	}
	s.publishLoot(EventMonsterLootClaimed, drop, playerID)
	return drop, inventory, nil
}

func (s *MonsterService) createLootDrop(ctx context.Context, item monster.Monster, now time.Time) error {
	loot := LootForMonster(item)
	if len(loot) == 0 {
		return nil
	}
	drop := monster.LootDrop{
		ID:        monster.LootDropID(fmt.Sprintf("monster_loot_%s_%d", item.ID, now.UnixNano())),
		MapID:     item.MapID,
		MonsterID: item.ID,
		Tile:      item.Tile,
		Items:     loot,
		CreatedAt: now,
	}
	if err := s.repo.CreateLootDrop(ctx, drop); err != nil {
		return err
	}
	s.publishLoot(EventMonsterLootDropped, drop, "")
	return nil
}

func (s *MonsterService) scheduleSpawnAfterDeath(ctx context.Context, item monster.Monster, now time.Time) error {
	if item.SpawnID == "" {
		return nil
	}
	spawns, err := s.repo.ListSpawnPoints(ctx, item.MapID)
	if err != nil {
		return err
	}
	for _, spawn := range spawns {
		if spawn.ID != item.SpawnID {
			continue
		}
		spawn.NextSpawnAt = now.Add(RandomSpawnCooldown())
		spawn.UpdatedAt = now
		return s.repo.SaveSpawnPoint(ctx, spawn)
	}
	return nil
}

func (s *MonsterService) publish(eventType EventType, item monster.Monster, playerID player.ID) {
	if s.events == nil {
		return
	}
	s.events.Publish(Event{
		Type:     eventType,
		ChunkID:  world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)),
		PlayerID: playerID,
		Payload:  MonsterPayload{Monster: item},
	})
}

func (s *MonsterService) publishLoot(eventType EventType, item monster.LootDrop, playerID player.ID) {
	if s.events == nil {
		return
	}
	s.events.Publish(Event{
		Type:     eventType,
		ChunkID:  world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)),
		PlayerID: playerID,
		Payload:  MonsterLootPayload{Loot: item},
	})
}

func LootForMonster(item monster.Monster) []economy.ResourceAmount {
	switch item.Type {
	case monster.TypeRoamingMelee:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 55, min: 55, max: 75},
			{resource: economy.ResourceWood, weight: 18, min: 18, max: 28},
			{resource: economy.ResourceTools, weight: 14, min: 1, max: 1},
			{resource: economy.ResourceRope, weight: 8, min: 2, max: 4},
			{resource: economy.ResourceExplosives, weight: 5, min: 1, max: 1},
		})
	case monster.TypeResourceGuardian:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 45, min: 100, max: 140},
			{resource: economy.ResourceStoneBlock, weight: 20, min: 3, max: 6},
			{resource: economy.ResourceIronIngot, weight: 15, min: 1, max: 3},
			{resource: economy.ResourceTools, weight: 12, min: 1, max: 2},
			{resource: economy.ResourceExplosives, weight: 8, min: 1, max: 2},
		})
	case monster.TypeRuinsGuardian:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 50, min: 190, max: 250},
			{resource: economy.ResourceExplosives, weight: 20, min: 2, max: 3},
			{resource: economy.ResourceTools, weight: 15, min: 2, max: 4},
			{resource: economy.ResourceEmeraldDust, weight: 10, min: 1, max: 1},
			{resource: economy.ResourceRuneTile, weight: 5, min: 1, max: 1},
		})
	case monster.TypeForestStalker:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 45, min: 45, max: 65},
			{resource: economy.ResourceWood, weight: 25, min: 24, max: 40},
			{resource: economy.ResourceResin, weight: 15, min: 4, max: 8},
			{resource: economy.ResourceHerbs, weight: 10, min: 6, max: 12},
			{resource: economy.ResourceElderwoodHeart, weight: 5, min: 1, max: 1},
		})
	case monster.TypeSporeBeast:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 40, min: 110, max: 150},
			{resource: economy.ResourceMushrooms, weight: 25, min: 12, max: 22},
			{resource: economy.ResourceHerbs, weight: 18, min: 10, max: 18},
			{resource: economy.ResourceRareFlowers, weight: 10, min: 1, max: 2},
			{resource: economy.ResourceSuperMushrooms, weight: 7, min: 1, max: 1},
		})
	case monster.TypeIronbackBrute:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 45, min: 280, max: 360},
			{resource: economy.ResourceIronIngot, weight: 20, min: 4, max: 8},
			{resource: economy.ResourceSteel, weight: 17, min: 2, max: 4},
			{resource: economy.ResourceArmorPlates, weight: 10, min: 1, max: 2},
			{resource: economy.ResourceExplosives, weight: 8, min: 2, max: 4},
		})
	case monster.TypeEmberWisp:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 42, min: 150, max: 210},
			{resource: economy.ResourceSulfur, weight: 20, min: 4, max: 8},
			{resource: economy.ResourceFuel, weight: 18, min: 4, max: 7},
			{resource: economy.ResourceExplosives, weight: 12, min: 1, max: 2},
			{resource: economy.ResourceLightCrystal, weight: 8, min: 1, max: 1},
		})
	case monster.TypeAncientColossus:
		return rollLoot([]lootOption{
			{resource: economy.ResourceCoins, weight: 38, min: 2200, max: 3200},
			{resource: economy.ResourceExplosives, weight: 22, min: 10, max: 16},
			{resource: economy.ResourceArmorPlates, weight: 18, min: 4, max: 7},
			{resource: economy.ResourceLightCrystal, weight: 12, min: 2, max: 4},
			{resource: economy.ResourceSuperMechanism, weight: 10, min: 1, max: 2},
		})
	}
	return []economy.ResourceAmount{{Resource: economy.ResourceCoins, Amount: item.LootCoins}}
}

func RandomSpawnCooldown() time.Duration {
	return time.Duration(60+rand.Intn(61)) * time.Second
}

func randomMonsterSpec() (monster.Spec, bool) {
	specs := catalog.MonsterSpecs()
	total := 0
	for _, spec := range specs {
		if spec.SpawnWeight > 0 {
			total += spec.SpawnWeight
		}
	}
	if total <= 0 {
		return monster.Spec{}, false
	}
	roll := rand.Intn(total)
	for _, spec := range specs {
		if spec.SpawnWeight <= 0 {
			continue
		}
		if roll < spec.SpawnWeight {
			return spec, true
		}
		roll -= spec.SpawnWeight
	}
	return specs[len(specs)-1], true
}

type lootOption struct {
	resource economy.ResourceType
	weight   int
	min      int
	max      int
}

func rollLoot(options []lootOption) []economy.ResourceAmount {
	total := 0
	for _, option := range options {
		if option.weight > 0 {
			total += option.weight
		}
	}
	if total <= 0 {
		return nil
	}
	roll := rand.Intn(total)
	for _, option := range options {
		if option.weight <= 0 {
			continue
		}
		if roll < option.weight {
			return []economy.ResourceAmount{{Resource: option.resource, Amount: randomAmount(option.min, option.max)}}
		}
		roll -= option.weight
	}
	last := options[len(options)-1]
	return []economy.ResourceAmount{{Resource: last.resource, Amount: randomAmount(last.min, last.max)}}
}

func randomAmount(minimum, maximum int) int {
	if minimum <= 0 {
		minimum = 1
	}
	if maximum < minimum {
		maximum = minimum
	}
	return minimum + rand.Intn(maximum-minimum+1)
}

type Reward struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}
