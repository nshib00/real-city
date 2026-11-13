package service

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
)

const cannonCooldown = 12 * time.Second

var errCannonShotConflict = errors.New("cannon shot state changed")

type CannonService struct {
	mu             sync.Mutex
	lastCheckedID  building.ID
	buildings      BuildingRepository
	monsters       MonsterRepository
	economy        EconomyRepository
	worlds         WorldRepository
	uow            UnitOfWork
	events         *EventBus
	monsterService *MonsterService
	economyService *EconomyService
	log            *slog.Logger
}

func NewCannonService(buildings BuildingRepository, monsters MonsterRepository, economy EconomyRepository, worlds WorldRepository, uow UnitOfWork, monsterService *MonsterService, economyService *EconomyService, events *EventBus, log *slog.Logger) *CannonService {
	return &CannonService{buildings: buildings, monsters: monsters, economy: economy, worlds: worlds, uow: uow, monsterService: monsterService, economyService: economyService, events: events, log: log}
}

func (s *CannonService) Tick(ctx context.Context, now time.Time, limit int) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	items, err := s.buildings.ListReadyCannons(ctx, DefaultWorldID, now, s.lastCheckedID, limit)
	if err != nil {
		return 0, err
	}
	if len(items) == 0 && s.lastCheckedID != "" {
		s.lastCheckedID = ""
		items, err = s.buildings.ListReadyCannons(ctx, DefaultWorldID, now, "", limit)
		if err != nil {
			return 0, err
		}
	}
	fired := 0
	for _, item := range items {
		s.lastCheckedID = item.ID
		if !cannonCanFire(item, now) {
			continue
		}
		shot, err := s.fire(ctx, item.ID, now)
		if errors.Is(err, errCannonShotConflict) {
			continue
		}
		if err != nil {
			return fired, err
		}
		if shot {
			fired++
		}
	}
	return fired, nil
}

func cannonCanFire(item building.Building, now time.Time) bool {
	if !catalog.IsDefenseWeapon(item.Type) || (item.State != building.StateActive && item.State != building.StateDamaged) || !item.CannonEnabled || item.Health <= 0 ||
		(item.CannonNextAttackAt != nil && item.CannonNextAttackAt.After(now)) {
		return false
	}
	spec, ok := catalog.GetBuilding(item.Type)
	if !ok {
		return false
	}
	for _, level := range spec.UpgradeLevels {
		if level.Level == item.Level {
			return item.Health*4 >= level.Health
		}
	}
	return false
}

func (s *CannonService) fire(ctx context.Context, id building.ID, now time.Time) (bool, error) {
	var fired bool
	var cannon building.Building
	var target monster.Monster
	var drop monster.LootDrop
	var ammo economy.ResourceType
	var dealt int
	work := func(txCtx context.Context) error {
		var err error
		cannon, err = s.buildings.FindByID(txCtx, id)
		if err != nil {
			return err
		}
		if !cannonCanFire(cannon, now) {
			return nil
		}
		stats, ok := catalog.DefenseWeaponLevel(cannon.Type, cannon.Level)
		if !ok {
			return nil
		}
		ammo = stats.Ammo
		target, ok, err = s.chooseTarget(txCtx, cannon, stats.Range)
		if err != nil || !ok {
			return err
		}
		if ammo != "" {
			spent, err := s.economy.SpendResourceIfAvailable(txCtx, player.ID(cannon.OwnerID), ammo, 1, now)
			if err != nil || !spent {
				return err
			}
		}
		claimed, err := s.buildings.ClaimCannonShot(txCtx, id, now, now.Add(stats.Cooldown), string(target.ID), cannon.Health)
		if err != nil {
			return err
		}
		if !claimed {
			return errCannonShotConflict
		}
		previous := target
		killed := target.ApplyDamage(stats.Damage, now)
		dealt = previous.Health - target.Health
		if !killed && (target.Type == monster.TypeForestStalker || target.Type == monster.TypeEmberWisp) &&
			(target.CreatorID == "" || target.CreatorID != cannon.OwnerID) && shouldRetaliateToCannon(txCtx, s.buildings, target) {
			target.State = monster.StateChase
			target.TargetID, target.TargetType = string(cannon.ID), "building"
			target.TargetTile, target.TargetLastSeenAt = cannon.Tile, now
		}
		if cannon.Type == building.TypeDefenseStormCoil && target.ShockUntil.Before(now.Add(2*time.Second)) {
			target.ShockUntil = now.Add(2 * time.Second)
		}
		updated, err := s.monsters.UpdateIfCurrent(txCtx, previous, target)
		if err != nil {
			return err
		}
		if !updated {
			return errCannonShotConflict
		}
		if ammo != "" {
			if err := s.economy.AddTransaction(txCtx, economy.Transaction{
				ID: economy.TransactionID(fmt.Sprintf("cannon_ammo_%s_%d", id, now.UnixNano())), PlayerID: cannon.OwnerID,
				Kind: economy.TransactionSpend, Resource: ammo, Amount: 1, Reason: "cannon:shot:" + string(id), CreatedAt: now,
			}); err != nil {
				return err
			}
		}
		if killed {
			loot := LootForMonster(target)
			if len(loot) > 0 {
				drop = monster.LootDrop{ID: monster.LootDropID(fmt.Sprintf("monster_loot_%s_%d", target.ID, now.UnixNano())), MapID: target.MapID, MonsterID: target.ID, Tile: target.Tile, Items: loot, CreatedAt: now}
				if err := s.monsters.CreateLootDrop(txCtx, drop); err != nil {
					return err
				}
			}
			if err := s.monsterService.scheduleSpawnAfterDeath(txCtx, target, now); err != nil {
				return err
			}
			if s.monsterService.experience != nil && target.CreatorID == "" {
				if spec, ok := catalog.MonsterSpec(target.Type); ok {
					if err := s.monsterService.experience.Award(txCtx, player.ID(cannon.OwnerID), max(1, spec.MaxHealth/10), "monster:kill", "monster:"+string(target.ID)+":kill"); err != nil {
						return err
					}
				}
			}
		}
		eventType := EventMonsterDamaged
		if killed {
			eventType = EventMonsterDied
		}
		if err := s.monsters.AddEvent(txCtx, monster.Event{ID: fmt.Sprintf("cannon_event_%s_%s_%d", id, target.ID, now.UnixNano()), MonsterID: target.ID, Type: string(eventType), TargetID: string(id), Tile: target.Tile, CreatedAt: now}); err != nil {
			return err
		}
		fired = true
		return nil
	}
	var err error
	uow := s.uow
	if uow == nil {
		repos := []any{s.buildings, s.monsters, s.economy}
		if s.monsterService != nil && s.monsterService.experience != nil {
			repos = append(repos, s.monsterService.experience.players)
		}
		uow = snapshotUnitOfWork{repos}
	}
	err = transactional(ctx, uow, work)
	if err != nil || !fired {
		return false, err
	}
	s.publishShot(ctx, cannon, target, drop, dealt)
	s.log.Info("defense_weapon.fired", "event", "defense_weapon.fired", "building_id", id, "monster_id", target.ID, "ammo", ammo, "damage", catalogDamage(cannon.Type, cannon.Level))
	return true, nil
}

func shouldRetaliateToCannon(ctx context.Context, buildings BuildingRepository, target monster.Monster) bool {
	if target.TargetType != "building" || target.TargetID == "" || buildings == nil {
		return true
	}
	current, err := buildings.FindByID(ctx, building.ID(target.TargetID))
	if err != nil {
		return true
	}
	spec, ok := catalog.GetBuilding(current.Type)
	return !ok || spec.Category != "defense"
}

func catalogDamage(kind building.Type, level int) int {
	stats, _ := catalog.DefenseWeaponLevel(kind, level)
	return stats.Damage
}

func (s *CannonService) chooseTarget(ctx context.Context, cannon building.Building, radius int) (monster.Monster, bool, error) {
	byID := make(map[monster.ID]monster.Monster)
	for _, dx := range []int{-worldgen.WorldSizeTiles, 0, worldgen.WorldSizeTiles} {
		for _, dy := range []int{-worldgen.WorldSizeTiles, 0, worldgen.WorldSizeTiles} {
			items, err := s.monsters.ListByViewport(ctx, cannon.MapID, cannon.Tile.X+dx-radius, cannon.Tile.Y+dy-radius, cannon.Tile.X+dx+radius, cannon.Tile.Y+dy+radius)
			if err != nil {
				return monster.Monster{}, false, err
			}
			for _, item := range items {
				byID[item.ID] = item
			}
		}
	}
	items := make([]monster.Monster, 0, len(byID))
	for _, item := range byID {
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool {
		a, b := items[i], items[j]
		da, db := defenseDistance(a.Tile, cannon.Tile), defenseDistance(b.Tile, cannon.Tile)
		if da != db {
			return da < db
		}
		if a.Health != b.Health {
			return a.Health < b.Health
		}
		return a.ID < b.ID
	})
	for _, item := range items {
		if !item.Alive() || (item.CreatorID != "" && item.CreatorID == cannon.OwnerID) || defenseDistance(item.Tile, cannon.Tile) > radius {
			continue
		}
		// The coil arcs to targets within range even when terrain or buildings
		// obstruct a direct projectile, including airborne monsters.
		if cannon.Type == building.TypeDefenseStormCoil {
			return item, true, nil
		}
		clear, err := s.lineOfSight(ctx, cannon, item.Tile)
		if err != nil {
			return monster.Monster{}, false, err
		}
		if clear {
			return item, true, nil
		}
	}
	return monster.Monster{}, false, nil
}

func defenseDistance(a, b world.Coord) int {
	return max(absInt(wrappedDefenseDelta(a.X, b.X)), absInt(wrappedDefenseDelta(a.Y, b.Y)))
}

func wrappedDefenseDelta(from, to int) int {
	delta := (to - from) % worldgen.WorldSizeTiles
	if delta > worldgen.WorldSizeTiles/2 {
		delta -= worldgen.WorldSizeTiles
	} else if delta < -worldgen.WorldSizeTiles/2 {
		delta += worldgen.WorldSizeTiles
	}
	return delta
}

func wrappedDefenseCoord(tile world.Coord) world.Coord {
	return world.Coord{X: ((tile.X % worldgen.WorldSizeTiles) + worldgen.WorldSizeTiles) % worldgen.WorldSizeTiles,
		Y: ((tile.Y % worldgen.WorldSizeTiles) + worldgen.WorldSizeTiles) % worldgen.WorldSizeTiles}
}

func (s *CannonService) lineOfSight(ctx context.Context, cannon building.Building, target world.Coord) (bool, error) {
	image := world.Coord{X: cannon.Tile.X + wrappedDefenseDelta(cannon.Tile.X, target.X), Y: cannon.Tile.Y + wrappedDefenseDelta(cannon.Tile.Y, target.Y)}
	line := cannonLine(cannon.Tile, image)
	if len(line) <= 2 {
		return true, nil
	}
	blockers := make(map[building.ID]building.Building)
	for _, dx := range []int{-worldgen.WorldSizeTiles, 0, worldgen.WorldSizeTiles} {
		for _, dy := range []int{-worldgen.WorldSizeTiles, 0, worldgen.WorldSizeTiles} {
			items, err := s.buildings.ListByViewport(ctx, cannon.MapID, min(cannon.Tile.X, image.X)+dx, min(cannon.Tile.Y, image.Y)+dy, max(cannon.Tile.X, image.X)+dx, max(cannon.Tile.Y, image.Y)+dy)
			if err != nil {
				return false, err
			}
			for _, item := range items {
				blockers[item.ID] = item
			}
		}
	}
	chunks := make(map[world.ChunkCoord]world.Chunk)
	for _, tile := range line[1 : len(line)-1] {
		for _, b := range blockers {
			if b.State == building.StateRuined || b.IsRoad() || building.IsTrapType(b.Type) {
				continue
			}
			for _, occupied := range b.OccupiedTiles() {
				if wrappedDefenseCoord(occupied) == wrappedDefenseCoord(tile) {
					return false, nil
				}
			}
		}
		groundTile := wrappedDefenseCoord(tile)
		coord := world.ChunkForTile(groundTile)
		chunk, ok := chunks[coord]
		if !ok {
			var err error
			chunk, _, err = s.worlds.GetOrCreateChunk(ctx, cannon.MapID, coord)
			if err != nil {
				return false, err
			}
			chunks[coord] = chunk
		}
		for _, ground := range chunk.Tiles {
			if ground.Coord == groundTile && ground.Terrain == world.TerrainMountain {
				return false, nil
			}
		}
	}
	return true, nil
}

func cannonLine(from, to world.Coord) []world.Coord {
	x, y := from.X, from.Y
	dx, dy := absInt(to.X-x), absInt(to.Y-y)
	sx, sy := 1, 1
	if x > to.X {
		sx = -1
	}
	if y > to.Y {
		sy = -1
	}
	err := dx - dy
	line := []world.Coord{{X: x, Y: y}}
	for x != to.X || y != to.Y {
		e2 := 2 * err
		if e2 > -dy {
			err -= dy
			x += sx
		}
		if e2 < dx {
			err += dx
			y += sy
		}
		line = append(line, world.Coord{X: x, Y: y})
	}
	return line
}

func absInt(n int) int {
	if n < 0 {
		return -n
	}
	return n
}

func (s *CannonService) publishShot(ctx context.Context, cannon building.Building, target monster.Monster, drop monster.LootDrop, damage int) {
	if s.events == nil {
		return
	}
	owner := player.ID(cannon.OwnerID)
	chunk := world.ChunkID(cannon.MapID, world.ChunkForTile(cannon.Tile))
	cannon.CannonTargetID = string(target.ID)
	stats, _ := catalog.DefenseWeaponLevel(cannon.Type, cannon.Level)
	next := target.UpdatedAt.Add(stats.Cooldown)
	cannon.CannonNextAttackAt = &next
	s.events.Publish(Event{Type: EventBuildingUpdated, ChunkID: chunk, PlayerID: owner, Payload: BuildingPayload{Building: cannon}})
	eventType := EventMonsterDamaged
	if !target.Alive() {
		eventType = EventMonsterDied
	}
	s.events.Publish(Event{Type: EventCannonShot, ChunkID: chunk, PlayerID: owner, Payload: CannonShotPayload{
		BuildingID: string(cannon.ID), BuildingType: string(cannon.Type), MonsterID: string(target.ID), Damage: damage,
		DamageType: stats.DamageType, Ammo: string(stats.Ammo), TileX: cannon.Tile.X, TileY: cannon.Tile.Y,
		TargetTileX: target.Tile.X, TargetTileY: target.Tile.Y,
	}})
	s.events.Publish(Event{Type: eventType, ChunkID: world.ChunkID(target.MapID, world.ChunkForTile(target.Tile)), PlayerID: owner, Payload: MonsterPayload{Monster: target, Damage: damage, Source: "cannon"}})
	if drop.ID != "" {
		s.events.Publish(Event{Type: EventMonsterLootDropped, ChunkID: world.ChunkID(drop.MapID, world.ChunkForTile(drop.Tile)), Payload: MonsterLootPayload{Loot: drop}})
	}
	if s.economyService != nil {
		inventory, err := s.economyService.Inventory(WithoutCatchUp(ctx), owner)
		if err == nil {
			s.events.Publish(Event{Type: EventInventoryChanged, PlayerID: owner, Payload: InventoryPayload{Inventory: inventory}})
		}
	}
}

func catalogAmmo(level int) economy.ResourceType {
	stats, _ := catalog.CannonLevel(level)
	return stats.Ammo
}
