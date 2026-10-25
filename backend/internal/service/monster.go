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
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

type MonsterService struct {
	repo       MonsterRepository
	log        *slog.Logger
	events     *EventBus
	economy    *EconomyService
	experience *ExperienceService
	now        func() time.Time
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

func (s *MonsterService) SetExperience(experience *ExperienceService) {
	s.experience = experience
}

func (s *MonsterService) Catalog(ctx context.Context) ([]monster.Spec, error) {
	_ = ctx
	return catalog.MonsterSpecs(), nil
}

func (s *MonsterService) List(ctx context.Context, center world.Coord, radius int) ([]monster.Monster, error) {
	if radius <= 0 {
		radius = 24
	}
	items, err := s.repo.ListByMap(ctx, DefaultWorldID)
	if err != nil {
		return nil, err
	}
	visible := make([]monster.Monster, 0, len(items))
	for _, item := range items {
		if wrappedTileDistance(item.Tile.X, center.X) <= radius && wrappedTileDistance(item.Tile.Y, center.Y) <= radius {
			visible = append(visible, item)
		}
	}
	return visible, nil
}

func wrappedTileDistance(left, right int) int {
	distance := (left - right) % worldgen.WorldSizeTiles
	if distance < 0 {
		distance += worldgen.WorldSizeTiles
	}
	if distance > worldgen.WorldSizeTiles/2 {
		distance = worldgen.WorldSizeTiles - distance
	}
	return distance
}

func (s *MonsterService) Get(ctx context.Context, id monster.ID) (monster.Monster, error) {
	return s.repo.FindByID(ctx, id)
}

func (s *MonsterService) Attack(ctx context.Context, id monster.ID, playerID player.ID) (monster.Monster, *monster.LootDrop, error) {
	return s.Damage(ctx, id, playerID, 28)
}

func (s *MonsterService) Damage(ctx context.Context, id monster.ID, playerID player.ID, damage int) (monster.Monster, *monster.LootDrop, error) {
	var item monster.Monster
	var killed bool
	var dealt int
	var now time.Time
	updated := false
	for attempt := 0; attempt < 3; attempt++ {
		previous, err := s.repo.FindByID(ctx, id)
		if err != nil {
			return monster.Monster{}, nil, err
		}
		if !previous.Alive() {
			return monster.Monster{}, nil, apperror.New(apperror.Conflict, "monster is already dead")
		}
		now = s.now()
		item = previous
		killed = item.ApplyDamage(damage, now)
		dealt = previous.Health - item.Health
		updated, err = s.repo.UpdateIfCurrent(ctx, previous, item)
		if err != nil {
			return monster.Monster{}, nil, err
		}
		if updated {
			break
		}
	}
	if !updated {
		return monster.Monster{}, nil, apperror.New(apperror.Conflict, "monster state changed; try again")
	}
	var drop *monster.LootDrop
	if killed {
		created, err := s.createLootDrop(ctx, item, now)
		if err != nil {
			return monster.Monster{}, nil, err
		}
		drop = &created
		if err := s.scheduleSpawnAfterDeath(ctx, item, now); err != nil {
			return monster.Monster{}, nil, err
		}
		if s.experience != nil {
			spec, ok := catalog.MonsterSpec(item.Type)
			if ok {
				key := "monster:" + string(item.ID) + ":kill"
				if err := s.experience.Award(ctx, playerID, max(1, spec.MaxHealth/10), "monster:kill", key); err != nil {
					return monster.Monster{}, nil, err
				}
			}
		}
	}
	eventType := EventMonsterDamaged
	if killed {
		eventType = EventMonsterDied
	}
	s.publish(eventType, item, playerID, dealt)
	_ = s.repo.AddEvent(ctx, monster.Event{ID: fmt.Sprintf("monster_event_%s_%d", item.ID, now.UnixNano()), MonsterID: item.ID, Type: string(eventType), TargetID: string(playerID), Tile: item.Tile, CreatedAt: now})
	s.log.Info("pve.monster.damaged", "event", "pve.monster.damaged", "monster_id", item.ID, "monster_type", item.Type, "player_id", playerID, "damage", damage, "dead", killed, "chunk_id", world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)))
	return item, drop, nil
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
	xRanges := lootViewportRanges(center.X, radius)
	yRanges := lootViewportRanges(center.Y, radius)
	items := make([]monster.LootDrop, 0)
	seen := make(map[monster.LootDropID]bool)
	for _, xRange := range xRanges {
		for _, yRange := range yRanges {
			part, err := s.repo.ListLootDropsByViewport(ctx, DefaultWorldID, xRange[0], yRange[0], xRange[1], yRange[1])
			if err != nil {
				return nil, err
			}
			for _, item := range part {
				if !seen[item.ID] {
					seen[item.ID] = true
					items = append(items, item)
				}
			}
		}
	}
	return items, nil
}

func lootViewportRanges(center, radius int) [][2]int {
	size := worldgen.WorldSizeTiles
	if radius >= size/2 {
		return [][2]int{{-size, 2*size - 1}}
	}
	center = (center%size + size) % size
	return [][2]int{
		{center - radius - size, center + radius - size},
		{center - radius, center + radius},
		{center - radius + size, center + radius + size},
	}
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

func (s *MonsterService) createLootDrop(ctx context.Context, item monster.Monster, now time.Time) (monster.LootDrop, error) {
	loot := LootForMonster(item)
	if len(loot) == 0 {
		return monster.LootDrop{}, nil
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
		return monster.LootDrop{}, err
	}
	s.publishLoot(EventMonsterLootDropped, drop, "")
	return drop, nil
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

func (s *MonsterService) publish(eventType EventType, item monster.Monster, playerID player.ID, damage ...int) {
	if s.events == nil {
		return
	}
	payload := MonsterPayload{Monster: item}
	if len(damage) > 0 && damage[0] > 0 {
		payload.Damage = damage[0]
		payload.Source = "player"
	}
	s.events.Publish(Event{
		Type:     eventType,
		ChunkID:  world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)),
		PlayerID: playerID,
		Payload:  payload,
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
		return rollLoot(roamingMeleeLootOptions)
	case monster.TypeResourceGuardian:
		return rollLoot(resourceGuardianLootOptions)
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

var roamingMeleeLootOptions = []lootOption{
	{resource: economy.ResourceCoins, weight: 42, min: 55, max: 75},
	{resource: economy.ResourceWood, weight: 25, min: 18, max: 28},
	{resource: economy.ResourceRope, weight: 20, min: 2, max: 4},
	{resource: economy.ResourceTools, weight: 8, min: 1, max: 1},
	{resource: economy.ResourceExplosives, weight: 5, min: 1, max: 1},
}

var resourceGuardianLootOptions = []lootOption{
	{resource: economy.ResourceCoins, weight: 30, min: 100, max: 140},
	{resource: economy.ResourceStone, weight: 25, min: 9, max: 15},
	{resource: economy.ResourceFiber, weight: 14, min: 3, max: 5},
	{resource: economy.ResourceStoneBlock, weight: 10, min: 3, max: 6},
	{resource: economy.ResourceTools, weight: 12, min: 1, max: 2},
	{resource: economy.ResourceExplosives, weight: 7, min: 1, max: 1},
	{resource: economy.ResourceIronIngot, weight: 2, min: 1, max: 2},
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
