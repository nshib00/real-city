package simulation

import (
	"context"
	"errors"
	"fmt"
	"hash/fnv"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service"
	"real-city/backend/internal/service/worldgen"
	"real-city/backend/pkg/apperror"
)

type MonsterAI struct {
	monsters              service.MonsterRepository
	buildings             service.BuildingRepository
	worlds                service.WorldRepository
	uow                   service.UnitOfWork
	experience            *service.ExperienceService
	buildingService       *service.BuildingService
	moveInterval          time.Duration
	specialAttacksEnabled bool
	events                *service.EventBus
	log                   *slog.Logger
}

var errMonsterTickConflict = errors.New("monster tick state changed")

const (
	monsterDetectionBonus      = 3
	monsterTargetLeashBonus    = 6
	monsterLostTargetMemory    = 20 * time.Second
	monsterInvestigationRadius = 2
	ironbackRamWindup          = 2 * time.Second
	emberVolleyWindup          = 1500 * time.Millisecond
)

func (ai *MonsterAI) SetUnitOfWork(uow service.UnitOfWork)                { ai.uow = uow }
func (ai *MonsterAI) SetExperience(experience *service.ExperienceService) { ai.experience = experience }

func (ai *MonsterAI) SetBuildingService(buildings *service.BuildingService) {
	ai.buildingService = buildings
}

func NewMonsterAI(monsters service.MonsterRepository, buildings service.BuildingRepository, worlds service.WorldRepository, events *service.EventBus, log *slog.Logger) *MonsterAI {
	return &MonsterAI{monsters: monsters, buildings: buildings, worlds: worlds, events: events, log: log, moveInterval: time.Second, specialAttacksEnabled: true}
}

func (ai *MonsterAI) SetSpecialAttacksEnabled(enabled bool) { ai.specialAttacksEnabled = enabled }

func (ai *MonsterAI) SetMoveInterval(interval time.Duration) {
	if interval > 0 {
		ai.moveInterval = interval
	}
}

func (ai *MonsterAI) Tick(ctx context.Context, now time.Time, limit int) (int, error) {
	items, err := ai.monsters.ListActiveForTick(ctx, service.DefaultWorldID, now, limit)
	if err != nil {
		return 0, err
	}
	chunkCache := make(map[world.ChunkCoord]world.Chunk)
	buildingCache := newTickBuildingCache(ai.buildings)
	assignedTargets := make(map[string]int)
	processed := 0
	for _, item := range items {
		if limit > 0 && processed >= limit {
			break
		}
		if !item.Alive() {
			continue
		}
		var updated monster.Monster
		var eventType service.EventType
		var targetID string
		var applied bool
		var activatedTraps []building.Building
		var damagedBuilding building.Building
		var actualDamage int
		var removedRuin bool
		var stateChanged bool
		work := func(txCtx context.Context) error {
			var path []world.Coord
			var trapOwner string
			var err error
			updated, eventType, targetID, path, err = ai.stepCached(txCtx, item, now, chunkCache, buildingCache, assignedTargets)
			if err != nil || updated.ID == "" {
				return err
			}
			if len(path) > 0 {
				trapOwner, activatedTraps, err = ai.applyTraps(txCtx, &updated, path, now)
				if err != nil {
					return err
				}
				if !updated.Alive() {
					eventType = service.EventMonsterDied
				} else if updated.Health < item.Health {
					eventType = service.EventMonsterDamaged
				}
			}
			comparison := updated
			comparison.UpdatedAt = item.UpdatedAt
			stateChanged = comparison != item
			applied, err = ai.monsters.UpdateIfCurrent(txCtx, item, updated)
			if err != nil {
				return err
			}
			if !applied {
				return errMonsterTickConflict
			}
			if eventType == service.EventMonsterAttacked && updated.TargetType == "building" {
				target, err := ai.buildings.FindByID(txCtx, building.ID(targetID))
				if err != nil {
					var appErr *apperror.Error
					if errors.As(err, &appErr) && appErr.Kind == apperror.NotFound {
						return errMonsterTickConflict
					}
					return err
				}
				if target.State == building.StateRuined || target.State == building.StatePlanned ||
					target.Health <= 0 || building.IsTrapType(target.Type) ||
					wrappedManhattan(updated.Tile, closestBuildingTile(updated.Tile, target)) > updated.AttackRange {
					return errMonsterTickConflict
				}
				if updated.CreatorID != "" && target.OwnerID == updated.CreatorID {
					return errMonsterTickConflict
				}
				var damaged bool
				damage := updated.Damage
				damage = ai.abilityDamage(updated.Type, target.Type, damage)
				if ai.buildingService != nil {
					damage, err = ai.buildingService.ProtectedDamage(txCtx, player.ID(target.OwnerID), damage)
					if err != nil {
						return err
					}
				}
				if ai.buildingService != nil && updated.CreatorID != "" {
					damage, err = ai.buildingService.PvPDamage(txCtx, target, player.ID(updated.CreatorID), damage, now)
					if err != nil {
						return err
					}
					if damage <= 0 {
						return nil
					}
				}
				damagedBuilding, damaged, err = ai.buildings.DamageIfCurrent(txCtx, target.ID, target.Health, damage, now, target.OwnerID)
				if err != nil {
					return err
				}
				if !damaged {
					return errMonsterTickConflict
				}
				if damagedBuilding.Type != target.Type || damagedBuilding.Level != target.Level {
					return errMonsterTickConflict
				}
				actualDamage = target.Health - damagedBuilding.Health
				if damagedBuilding.State == building.StateRuined && ai.buildingService != nil {
					if err := ai.buildingService.HandleDestruction(txCtx, target, damagedBuilding, player.ID(updated.CreatorID), now); err != nil {
						return err
					}
					removedRuin = true
				} else if damagedBuilding.State == building.StateRuined {
					if err := ai.buildings.Delete(txCtx, damagedBuilding.ID); err != nil {
						return err
					}
					removedRuin = true
				}
				if ai.buildingService != nil {
					if err := ai.buildingService.RecordBuildingAttack(txCtx, target, damagedBuilding, player.ID(updated.CreatorID), "monster:"+string(updated.Type), fmt.Sprintf("%s:%d", updated.ID, now.UnixNano()), now); err != nil {
						return err
					}
				}
			}
			if eventType == service.EventMonsterDied {
				if err := ai.createLootDrop(txCtx, updated, now); err != nil {
					return err
				}
				if err := ai.scheduleSpawnAfterDeath(txCtx, updated, now); err != nil {
					return err
				}
				if trapOwner != "" && ai.experience != nil && updated.CreatorID == "" {
					if spec, ok := catalog.MonsterSpec(updated.Type); ok {
						if err := ai.experience.Award(txCtx, player.ID(trapOwner), max(1, spec.MaxHealth/10), "monster:kill", "monster:"+string(updated.ID)+":kill"); err != nil {
							return err
						}
					}
				}
			}
			if eventType != service.EventMonsterMoved {
				return ai.monsters.AddEvent(txCtx, monster.Event{ID: fmt.Sprintf("monster_event_%s_%d", updated.ID, now.UnixNano()), MonsterID: updated.ID, Type: string(eventType), TargetID: targetID, Tile: updated.Tile, CreatedAt: now})
			}
			return nil
		}
		var err error
		if ai.buildingService != nil {
			err = ai.buildingService.DestructionTransaction(ctx, ai.uow, work, ai.monsters)
		} else if ai.uow != nil {
			err = ai.uow.Do(ctx, work)
		} else {
			err = work(ctx)
		}
		if errors.Is(err, errMonsterTickConflict) {
			buildingCache.clear()
			continue
		}
		if err != nil {
			return processed, err
		}
		if !applied {
			continue
		}
		if damagedBuilding.ID != "" {
			buildingCache.clear()
		}
		if ai.events != nil {
			if damagedBuilding.ID != "" {
				if removedRuin {
					ai.events.Publish(service.Event{Type: service.EventBuildingRemoved, ChunkID: world.ChunkID(damagedBuilding.MapID, world.ChunkForTile(damagedBuilding.Tile)), PlayerID: player.ID(damagedBuilding.OwnerID), Payload: service.BuildingRemovedPayload{BuildingID: damagedBuilding.ID, Reason: "monster_attack", Damage: actualDamage, TileX: damagedBuilding.Tile.X, TileY: damagedBuilding.Tile.Y, BuildingType: damagedBuilding.Type}})
				} else {
					ai.events.Publish(service.Event{Type: service.EventBuildingUpdated, ChunkID: world.ChunkID(damagedBuilding.MapID, world.ChunkForTile(damagedBuilding.Tile)), PlayerID: player.ID(damagedBuilding.OwnerID), Payload: service.BuildingPayload{Building: damagedBuilding, Reason: "monster_attack", Damage: actualDamage}})
				}
			}
			for _, trap := range activatedTraps {
				ai.events.Publish(service.Event{Type: service.EventBuildingUpdated, ChunkID: world.ChunkID(trap.MapID, world.ChunkForTile(trap.Tile)), PlayerID: player.ID(trap.OwnerID), Payload: service.BuildingPayload{Building: trap}})
				ai.events.Publish(service.Event{Type: service.EventDefenseTriggered, ChunkID: world.ChunkID(trap.MapID, world.ChunkForTile(trap.Tile)), PlayerID: player.ID(trap.OwnerID), Payload: service.DefenseTriggeredPayload{BuildingID: string(trap.ID), BuildingType: string(trap.Type), MonsterID: string(updated.ID), TileX: trap.Tile.X, TileY: trap.Tile.Y}})
			}
		}
		if stateChanged || eventType != service.EventMonsterMoved {
			ai.publish(eventType, updated, max(0, item.Health-updated.Health))
		}
		ai.log.Debug("pve.monster.tick", "event", "pve.monster.tick", "monster_id", updated.ID, "monster_type", updated.Type, "state", updated.State, "target_id", targetID, "chunk_id", world.ChunkID(updated.MapID, world.ChunkForTile(updated.Tile)))
		processed++
		if updated.TargetType == "building" && updated.TargetID != "" {
			assignedTargets[updated.TargetID]++
		}
	}
	return processed, nil
}

func (ai *MonsterAI) step(ctx context.Context, item monster.Monster, now time.Time, chunkCache map[world.ChunkCoord]world.Chunk) (monster.Monster, service.EventType, string, []world.Coord, error) {
	return ai.stepCached(ctx, item, now, chunkCache, nil, nil)
}

func (ai *MonsterAI) retainedTarget(ctx context.Context, item *monster.Monster, now time.Time) (building.Building, bool, world.Coord, bool, error) {
	if item.TargetType != "building" || item.TargetID == "" {
		return building.Building{}, false, world.Coord{}, false, nil
	}
	if ai.buildings == nil {
		return building.Building{}, false, item.TargetTile, !item.TargetLastSeenAt.IsZero() && now.Sub(item.TargetLastSeenAt) <= monsterLostTargetMemory, nil
	}
	if item.TargetLastSeenAt.IsZero() {
		item.TargetLastSeenAt = item.UpdatedAt
	}
	target, err := ai.buildings.FindByID(ctx, building.ID(item.TargetID))
	if err == nil && target.State != building.StateRuined && target.State != building.StatePlanned && target.Health > 0 && !building.IsTrapType(target.Type) {
		tile := closestBuildingTile(item.Tile, target)
		item.TargetTile = tile
		if wrappedManhattan(item.Tile, tile) <= max(0, item.AggroRadius+monsterTargetLeashBonus) {
			item.TargetLastSeenAt = now
			return target, true, tile, false, nil
		}
	} else if err != nil {
		var appErr *apperror.Error
		if !errors.As(err, &appErr) || appErr.Kind != apperror.NotFound {
			return building.Building{}, false, world.Coord{}, false, err
		}
	}
	if now.Sub(item.TargetLastSeenAt) <= monsterLostTargetMemory {
		return building.Building{}, false, item.TargetTile, true, nil
	}
	item.TargetID, item.TargetType = "", ""
	item.TargetTile, item.TargetLastSeenAt = world.Coord{}, time.Time{}
	return building.Building{}, false, world.Coord{}, false, nil
}

func (ai *MonsterAI) stepCached(ctx context.Context, item monster.Monster, now time.Time, chunkCache map[world.ChunkCoord]world.Chunk, buildingCache *tickBuildingCache, assignedTargets map[string]int) (monster.Monster, service.EventType, string, []world.Coord, error) {
	ctx = context.WithValue(ctx, monsterTargetCacheKey{}, &monsterTargetCache{assignedTargets: assignedTargets})
	if item.CreatorID != "" && !item.ExpiresAt.After(now) {
		item.State, item.Health, item.UpdatedAt = monster.StateDead, 0, now
		return item, service.EventMonsterDespawned, "", nil, nil
	}
	origin := item.Tile
	excluded := make(map[building.ID]bool)
	target, ok, investigateTile, investigating, err := ai.retainedTarget(ctx, &item, now)
	if err != nil {
		return monster.Monster{}, "", "", nil, err
	}
	if !ok && !investigating && ai.buildings != nil {
		search := item
		search.AggroRadius += monsterDetectionBonus
		target, ok, err = ai.nearestTargetExceptCached(ctx, search, excluded, buildingCache)
		if err != nil {
			return monster.Monster{}, "", "", nil, err
		}
		if ok {
			item.TargetID, item.TargetType = string(target.ID), "building"
			item.TargetTile = closestBuildingTile(item.Tile, target)
			item.TargetLastSeenAt = now
		}
	}
	item.UpdatedAt = now
	for ok {
		isWindingUp := item.State == monster.StateWindup
		targetTile := closestBuildingTile(item.Tile, target)
		lineOfSight := true
		if item.Type == monster.TypeEmberWisp {
			lineOfSight, err = ai.clearShotToBuilding(ctx, item, target, targetTile, chunkCache, buildingCache)
			if err != nil {
				return monster.Monster{}, "", "", nil, err
			}
		}
		item.State = monster.StateChase
		item.TargetID = string(target.ID)
		item.TargetType = "building"
		item.TargetTile = targetTile
		item.TargetLastSeenAt = now
		if item.Alive() && wrappedManhattan(item.Tile, targetTile) <= item.AttackRange && lineOfSight && !item.NextAttackAt.After(now) && !item.ShockUntil.After(now) {
			if windup := ai.attackWindup(item.Type, target.Type); windup > 0 && !isWindingUp {
				item.State = monster.StateWindup
				item.NextAttackAt = now.Add(windup)
				return item, service.EventMonsterMoved, string(target.ID), nil, nil
			}
			if isWindingUp && item.NextAttackAt.After(now) {
				item.State = monster.StateWindup
				return item, service.EventMonsterMoved, string(target.ID), nil, nil
			}
			item.State = monster.StateAttacking
			item.NextAttackAt = now.Add(item.AttackCooldown)
			return item, service.EventMonsterAttacked, string(target.ID), nil, nil
		}
		if isWindingUp && item.NextAttackAt.After(now) {
			item.State = monster.StateWindup
			return item, service.EventMonsterMoved, string(target.ID), nil, nil
		}
		if wrappedManhattan(item.Tile, targetTile) <= item.AttackRange && lineOfSight {
			item.State = monster.StateRecover
			return item, service.EventMonsterMoved, string(target.ID), nil, nil
		}
		if item.LastMovedAt.After(now) {
			return item, service.EventMonsterMoved, string(target.ID), nil, nil
		}
		pathItem := item
		if !lineOfSight && item.Type == monster.TypeEmberWisp {
			pathItem.AttackRange = 1
		}
		path, err := ai.pathToBuildingContact(ctx, pathItem, target, chunkCache, buildingCache)
		if err != nil {
			return monster.Monster{}, "", "", nil, err
		}
		if len(path) == 0 {
			excluded[target.ID] = true
			search := item
			search.AggroRadius += monsterDetectionBonus
			target, ok, err = ai.nearestTargetExceptCached(ctx, search, excluded, buildingCache)
			if err != nil {
				return monster.Monster{}, "", "", nil, err
			}
			continue
		}
		if len(path) > 0 {
			item.Tile = path[len(path)-1]
		}
		item.LastMovedAt = now
		return item, service.EventMonsterMoved, string(target.ID), path, nil
	}
	if investigating {
		item.State = monster.StateInvestigate
		if wrappedManhattan(item.Tile, investigateTile) > monsterInvestigationRadius && !item.LastMovedAt.After(now) {
			path, err := ai.nextPassablePathCached(ctx, item.Tile, investigateTile, item.SpeedTiles, monsterInvestigationRadius, item.Type == monster.TypeEmberWisp, chunkCache, buildingCache)
			if err != nil {
				return monster.Monster{}, "", "", nil, err
			}
			if len(path) > 0 {
				item.Tile = path[len(path)-1]
				item.LastMovedAt = now
				return item, service.EventMonsterMoved, item.TargetID, path, nil
			}
		}
		if now.Sub(item.TargetLastSeenAt) <= monsterLostTargetMemory {
			return item, service.EventMonsterMoved, item.TargetID, nil, nil
		}
		item.TargetID, item.TargetType = "", ""
		item.TargetTile, item.TargetLastSeenAt = world.Coord{}, time.Time{}
	}
	if targetMonster, ok, err := ai.collidingMonster(ctx, item); err != nil {
		return monster.Monster{}, "", "", nil, err
	} else if ok && item.CanAttack(now, targetMonster.Tile) {
		previousTarget := targetMonster
		targetMonster.ApplyDamage(item.Damage, now)
		applied, err := ai.monsters.UpdateIfCurrent(ctx, previousTarget, targetMonster)
		if err != nil {
			return monster.Monster{}, "", "", nil, err
		}
		if !applied {
			return monster.Monster{}, "", "", nil, nil
		}
		if targetMonster.State == monster.StateDead {
			if err := ai.createLootDrop(ctx, targetMonster, now); err != nil {
				return monster.Monster{}, "", "", nil, err
			}
			if err := ai.scheduleSpawnAfterDeath(ctx, targetMonster, now); err != nil {
				return monster.Monster{}, "", "", nil, err
			}
		}
		item.State = monster.StateAttacking
		item.TargetID = string(targetMonster.ID)
		item.TargetType = "monster"
		item.NextAttackAt = now.Add(item.AttackCooldown)
		return item, service.EventMonsterAttacked, string(targetMonster.ID), nil, nil
	}
	item.State = monster.StateWandering
	item.TargetID = ""
	item.TargetType = ""
	item.TargetTile, item.TargetLastSeenAt = world.Coord{}, time.Time{}
	if item.LastMovedAt.After(now) {
		return item, service.EventMonsterMoved, "", nil, nil
	}
	wander := monster.WanderFrom(item.HomeTile, now.Unix()+int64(len(item.ID)), 5)
	path, err := ai.nextPassablePathCached(ctx, item.Tile, wander, item.SpeedTiles, 0, item.Type == monster.TypeEmberWisp, chunkCache, buildingCache)
	if err != nil {
		return monster.Monster{}, "", "", nil, err
	}
	if len(path) > 0 {
		item.Tile = path[len(path)-1]
	}
	item.LastMovedAt = now
	if item.Tile != origin {
		return item, service.EventMonsterMoved, "", path, nil
	}
	return item, service.EventMonsterMoved, "", nil, nil
}

func monsterAttackWindup(monsterType monster.Type, targetType building.Type) time.Duration {
	switch monsterType {
	case monster.TypeIronbackBrute:
		if isMonsterRamTarget(targetType) {
			return ironbackRamWindup
		}
	case monster.TypeEmberWisp:
		return emberVolleyWindup
	}
	return 0
}

func (ai *MonsterAI) attackWindup(monsterType monster.Type, targetType building.Type) time.Duration {
	if !ai.specialAttacksEnabled {
		return 0
	}
	return monsterAttackWindup(monsterType, targetType)
}

func monsterAbilityDamage(monsterType monster.Type, targetType building.Type, damage int) int {
	switch monsterType {
	case monster.TypeIronbackBrute:
		if isMonsterRamTarget(targetType) {
			return damage * 2
		}
	case monster.TypeEmberWisp:
		if spec, ok := catalog.GetBuilding(targetType); ok && (spec.Category == "industry" || spec.Category == "fields") {
			return damage * 3 / 2
		}
	}
	return damage
}

func (ai *MonsterAI) abilityDamage(monsterType monster.Type, targetType building.Type, damage int) int {
	if !ai.specialAttacksEnabled {
		return damage
	}
	return monsterAbilityDamage(monsterType, targetType, damage)
}

func isMonsterRamTarget(targetType building.Type) bool {
	switch targetType {
	case building.TypeWoodenWall, building.TypeStoneWall, building.TypeConcreteWall, building.TypeModernWall:
		return true
	default:
		return false
	}
}

func (ai *MonsterAI) nearestTarget(ctx context.Context, item monster.Monster) (building.Building, bool, error) {
	return ai.nearestTargetExcept(ctx, item, nil)
}

func (ai *MonsterAI) nearestTargetExcept(ctx context.Context, item monster.Monster, excluded map[building.ID]bool) (building.Building, bool, error) {
	return ai.nearestTargetExceptCached(ctx, item, excluded, nil)
}

func (ai *MonsterAI) nearestTargetExceptCached(ctx context.Context, item monster.Monster, excluded map[building.ID]bool, buildingCache *tickBuildingCache) (building.Building, bool, error) {
	radius := max(0, item.AggroRadius)
	center := wrappedCoord(item.Tile)
	cache, _ := ctx.Value(monsterTargetCacheKey{}).(*monsterTargetCache)
	var buildings []building.Building
	if cache != nil && cache.loaded {
		buildings = cache.buildings
	} else {
		buildings = make([]building.Building, 0)
		seen := make(map[building.ID]bool)
		for _, offsetX := range viewportOffsets(center.X, radius) {
			for _, offsetY := range viewportOffsets(center.Y, radius) {
				minX, minY := center.X+offsetX-radius, center.Y+offsetY-radius
				maxX, maxY := center.X+offsetX+radius, center.Y+offsetY+radius
				items, err := ai.buildingsInRect(ctx, item.MapID, minX, minY, maxX, maxY, buildingCache)
				if err != nil {
					return building.Building{}, false, err
				}
				for _, candidate := range items {
					if !seen[candidate.ID] {
						buildings = append(buildings, candidate)
						seen[candidate.ID] = true
					}
				}
			}
		}
		if cache != nil {
			cache.buildings, cache.loaded = buildings, true
		}
	}
	var best building.Building
	bestDistance := 0
	bestPreferred := false
	var assignedTargets map[string]int
	if cache != nil {
		assignedTargets = cache.assignedTargets
	}
	var bestDefense building.Building
	bestDefenseDistance := 0
	for _, target := range buildings {
		if (item.CreatorID != "" && target.OwnerID == item.CreatorID) || excluded[target.ID] || target.State == building.StateRuined || target.State == building.StatePlanned || target.Health <= 0 || building.IsTrapType(target.Type) {
			continue
		}
		distance := wrappedManhattan(item.Tile, closestBuildingTile(item.Tile, target))
		if distance > radius {
			continue
		}
		preferred := catalog.MonsterPrefersBuilding(item.Type, target.Type)
		score := targetScore(item, target, distance, preferred, buildings, assignedTargets)
		if isDefenseTarget(target.Type) && (bestDefense.ID == "" || distance < bestDefenseDistance || distance == bestDefenseDistance && target.ID < bestDefense.ID) {
			bestDefense, bestDefenseDistance = target, distance
		}
		bestScore := -int(^uint(0) >> 1)
		if best.ID != "" {
			bestScore = targetScore(item, best, bestDistance, bestPreferred, buildings, assignedTargets)
		}
		if best.ID == "" || score > bestScore || score == bestScore && target.ID < best.ID {
			best = target
			bestDistance = distance
			bestPreferred = preferred
		}
	}
	if !bestPreferred && bestDefense.ID != "" && best.ID != bestDefense.ID && defenseRoll(item.ID) < 3 {
		best = bestDefense
	}
	return best, best.ID != "", nil
}

type monsterTargetCacheKey struct{}
type monsterTargetCache struct {
	buildings       []building.Building
	loaded          bool
	assignedTargets map[string]int
}

func targetScore(item monster.Monster, target building.Building, distance int, preferred bool, nearby []building.Building, assigned map[string]int) int {
	score := -distance * 24
	if preferred {
		score += 1000
	}
	if spec, ok := catalog.GetBuilding(target.Type); ok {
		switch spec.Category {
		case "center":
			score += 220
		case "housing":
			score += 100
		case "industry", "fields", "storage", "trade", "resource":
			score += 80
		case "defense":
			score += 65
		}
		if spec.Health > 0 && target.Health > 0 {
			damageTaken := max(0, spec.Health-target.Health)
			score += min(40, damageTaken*40/spec.Health)
		}
	}
	for _, guard := range nearby {
		if guard.ID != target.ID && isDefenseTarget(guard.Type) && wrappedManhattan(closestBuildingTile(target.Tile, target), closestBuildingTile(target.Tile, guard)) <= 2 {
			score -= 45
		}
	}
	if item.Type != monster.TypeIronbackBrute {
		score -= min(3, assigned[string(target.ID)]) * 180
	}
	return score
}

func (ai *MonsterAI) pathToBuildingContact(ctx context.Context, item monster.Monster, target building.Building, chunkCache map[world.ChunkCoord]world.Chunk, buildingCache *tickBuildingCache) ([]world.Coord, error) {
	contacts := target.OccupiedTiles()
	if len(contacts) == 0 {
		contacts = []world.Coord{target.Tile}
	}
	var best []world.Coord
	for _, contact := range contacts {
		path, err := ai.nextPassablePathCached(ctx, item.Tile, contact, item.SpeedTiles, item.AttackRange, item.Type == monster.TypeEmberWisp, chunkCache, buildingCache)
		if err != nil {
			return nil, err
		}
		if len(path) > 0 && (best == nil || len(path) < len(best) || len(path) == len(best) && (path[len(path)-1].X < best[len(best)-1].X || path[len(path)-1].X == best[len(best)-1].X && path[len(path)-1].Y < best[len(best)-1].Y)) {
			best = path
		}
	}
	return best, nil
}

func isDefenseTarget(kind building.Type) bool {
	switch kind {
	case building.TypeDefenseCannon, building.TypeDefenseBoltThrower, building.TypeDefenseStormCoil,
		building.TypeTower, building.TypeWoodenWall, building.TypeStoneWall,
		building.TypeConcreteWall, building.TypeModernWall:
		return true
	}
	return false
}

func defenseRoll(id monster.ID) uint32 {
	h := fnv.New32a()
	_, _ = h.Write([]byte(id))
	return h.Sum32() % 4
}

func closestBuildingTile(from world.Coord, target building.Building) world.Coord {
	best := target.Tile
	bestDistance := wrappedManhattan(from, best)
	for _, occupied := range target.OccupiedTiles() {
		if distance := wrappedManhattan(from, occupied); distance < bestDistance {
			best, bestDistance = occupied, distance
		}
	}
	return best
}

func wrappedManhattan(a, b world.Coord) int { return world.WrappedManhattan(a, b) }

func viewportOffsets(coordinate, radius int) []int {
	offsets := []int{0}
	if coordinate < radius {
		offsets = append(offsets, worldgen.WorldSizeTiles)
	}
	if coordinate >= worldgen.WorldSizeTiles-radius {
		offsets = append(offsets, -worldgen.WorldSizeTiles)
	}
	return offsets
}

func (ai *MonsterAI) collidingMonster(ctx context.Context, item monster.Monster) (monster.Monster, bool, error) {
	items, err := ai.monsters.ListByViewport(ctx, item.MapID, item.Tile.X-1, item.Tile.Y-1, item.Tile.X+1, item.Tile.Y+1)
	if err != nil {
		return monster.Monster{}, false, err
	}
	var best monster.Monster
	bestDistance := 0
	for _, other := range items {
		if other.ID == item.ID || !other.Alive() || item.CreatorID != "" {
			continue
		}
		distance := item.DistanceTo(other.Tile)
		if distance > item.AttackRange {
			continue
		}
		if best.ID == "" || distance < bestDistance {
			best = other
			bestDistance = distance
		}
	}
	return best, best.ID != "", nil
}

func (ai *MonsterAI) nextPassablePath(ctx context.Context, from world.Coord, to world.Coord, speed, attackRange int, chunkCache map[world.ChunkCoord]world.Chunk) ([]world.Coord, error) {
	return ai.nextPassablePathCached(ctx, from, to, speed, attackRange, false, chunkCache, nil)
}

func (ai *MonsterAI) nextPassablePathCached(ctx context.Context, from world.Coord, to world.Coord, speed, attackRange int, flying bool, chunkCache map[world.ChunkCoord]world.Chunk, buildingCache *tickBuildingCache) (result []world.Coord, resultErr error) {
	started := time.Now()
	visited, maxQueue, failed := 0, 0, false
	defer func() { observability.MonsterPathSearch(started, visited, maxQueue, failed || resultErr != nil) }()
	from, to = wrappedCoord(from), wrappedCoord(to)
	if wrappedManhattan(from, to) <= attackRange {
		return nil, nil
	}
	searchRadius := min(28, max(12, wrappedManhattan(from, to)+8))
	occupied := make(map[world.Coord]bool)
	if ai.buildings != nil {
		for _, offsetX := range viewportOffsets(from.X, searchRadius) {
			for _, offsetY := range viewportOffsets(from.Y, searchRadius) {
				minX, minY := from.X+offsetX-searchRadius, from.Y+offsetY-searchRadius
				maxX, maxY := from.X+offsetX+searchRadius, from.Y+offsetY+searchRadius
				buildings, err := ai.buildingsInRect(ctx, service.DefaultWorldID, minX, minY, maxX, maxY, buildingCache)
				if err != nil {
					return nil, err
				}
				for _, item := range buildings {
					if building.IsTrapType(item.Type) {
						continue
					}
					if flying && item.Type != building.TypeConcreteWall && item.Type != building.TypeModernWall {
						continue
					}
					for _, tile := range item.OccupiedTiles() {
						occupied[wrappedCoord(tile)] = true
					}
				}
			}
		}
	}
	queue := []world.Coord{from}
	parents := map[world.Coord]world.Coord{from: from}
	directions := []world.Coord{{X: 1}, {X: -1}, {Y: 1}, {Y: -1}}
	for head := 0; head < len(queue) && head < 2048; head++ {
		visited++
		maxQueue = max(maxQueue, len(queue)-head)
		current := queue[head]
		if current != from && wrappedManhattan(current, to) <= attackRange {
			path := []world.Coord{}
			for current != from {
				path = append(path, current)
				current = parents[current]
			}
			for i, j := 0, len(path)-1; i < j; i, j = i+1, j-1 {
				path[i], path[j] = path[j], path[i]
			}
			return path[:min(len(path), max(1, speed))], nil
		}
		for _, direction := range directions {
			candidate := wrappedCoord(world.Coord{X: current.X + direction.X, Y: current.Y + direction.Y})
			if wrappedManhattan(candidate, world.Coord{X: from.X, Y: candidate.Y}) > searchRadius ||
				wrappedManhattan(candidate, world.Coord{X: candidate.X, Y: from.Y}) > searchRadius || occupied[candidate] {
				continue
			}
			if _, seen := parents[candidate]; seen {
				continue
			}
			passable, err := ai.isPassable(ctx, candidate, chunkCache)
			if err != nil {
				return nil, err
			}
			if passable {
				parents[candidate] = current
				queue = append(queue, candidate)
			}
		}
	}
	failed = true
	return nil, nil
}

func (ai *MonsterAI) applyTraps(ctx context.Context, item *monster.Monster, path []world.Coord, now time.Time) (string, []building.Building, error) {
	var activated []building.Building
	for _, tile := range path {
		item.Tile = tile
		items, err := ai.buildings.ListByViewport(ctx, item.MapID, tile.X, tile.Y, tile.X, tile.Y)
		if err != nil {
			return "", nil, err
		}
		for _, trap := range items {
			if item.CreatorID != "" && trap.OwnerID == item.CreatorID {
				continue
			}
			if !building.IsTrapType(trap.Type) || trap.Tile != tile || trap.TrapCharges < 1 {
				continue
			}
			stats, ok := catalog.DefenseTrapLevel(trap.Type, trap.Level)
			if !ok {
				continue
			}
			buildingSpec, ok := catalog.GetBuilding(trap.Type)
			if !ok || trap.Health <= 0 {
				continue
			}
			for _, level := range buildingSpec.UpgradeLevels {
				if level.Level == trap.Level && trap.Health*4 < level.Health {
					ok = false
				}
			}
			if !ok {
				continue
			}
			claimed, err := ai.buildings.ConsumeTrapCharge(ctx, trap.ID, trap.Health)
			if err != nil {
				return "", nil, err
			}
			if !claimed {
				continue
			}
			trap.TrapCharges--
			activated = append(activated, trap)
			if stats.SlowsNextStep {
				item.LastMovedAt = now.Add(ai.moveInterval * 3 / 2)
			}
			if item.ApplyDamage(stats.Damage, now) {
				return trap.OwnerID, activated, nil
			}
		}
	}
	return "", activated, nil
}

func (ai *MonsterAI) isPassable(ctx context.Context, tile world.Coord, chunkCache map[world.ChunkCoord]world.Chunk) (bool, error) {
	if ai.worlds == nil {
		return true, nil
	}
	chunkCoord := world.ChunkForTile(tile)
	chunk, ok := chunkCache[chunkCoord]
	if !ok {
		loaded, _, err := ai.worlds.GetOrCreateChunk(ctx, service.DefaultWorldID, chunkCoord)
		if err != nil {
			return false, err
		}
		chunk = loaded
		chunkCache[chunkCoord] = loaded
	}
	local := world.TileLocalCoord(tile)
	index := local.Y*world.ChunkSize + local.X
	if len(chunk.Tiles) == world.ChunkSize*world.ChunkSize && chunk.Tiles[index].Coord == tile {
		return chunk.Tiles[index].Terrain == world.TerrainGrass, nil
	}
	for _, item := range chunk.Tiles {
		if item.Coord == tile {
			return item.Terrain == world.TerrainGrass, nil
		}
	}
	return false, nil
}

func (ai *MonsterAI) clearShotToBuilding(ctx context.Context, item monster.Monster, target building.Building, targetTile world.Coord, chunkCache map[world.ChunkCoord]world.Chunk, buildingCache *tickBuildingCache) (bool, error) {
	dx, dy := targetTile.X-item.Tile.X, targetTile.Y-item.Tile.Y
	if dx > world.WorldSize/2 {
		dx -= world.WorldSize
	} else if dx < -world.WorldSize/2 {
		dx += world.WorldSize
	}
	if dy > world.WorldSize/2 {
		dy -= world.WorldSize
	} else if dy < -world.WorldSize/2 {
		dy += world.WorldSize
	}
	absDX, absDY := dx, dy
	if absDX < 0 {
		absDX = -absDX
	}
	if absDY < 0 {
		absDY = -absDY
	}
	steps := max(absDX, absDY)
	if steps < 2 {
		return true, nil
	}
	for step := 1; step < steps; step++ {
		tile := wrappedCoord(world.Coord{X: item.Tile.X + dx*step/steps, Y: item.Tile.Y + dy*step/steps})
		passable, err := ai.isPassable(ctx, tile, chunkCache)
		if err != nil {
			return false, err
		}
		if !passable {
			return false, nil
		}
		if ai.buildings == nil {
			continue
		}
		items, err := ai.buildingsInRect(ctx, item.MapID, tile.X, tile.Y, tile.X, tile.Y, buildingCache)
		if err != nil {
			return false, err
		}
		for _, obstacle := range items {
			if obstacle.ID != target.ID && !building.IsTrapType(obstacle.Type) && obstacle.State != building.StateRuined {
				for _, occupied := range obstacle.OccupiedTiles() {
					if wrappedCoord(occupied) == tile {
						return false, nil
					}
				}
			}
		}
	}
	return true, nil
}

func (ai *MonsterAI) createLootDrop(ctx context.Context, item monster.Monster, now time.Time) error {
	loot := service.LootForMonster(item)
	if len(loot) == 0 {
		return nil
	}
	return ai.monsters.CreateLootDrop(ctx, monster.LootDrop{
		ID:        monster.LootDropID(fmt.Sprintf("monster_loot_%s_%d", item.ID, now.UnixNano())),
		MapID:     item.MapID,
		MonsterID: item.ID,
		Tile:      item.Tile,
		Items:     loot,
		CreatedAt: now,
	})
}

func (ai *MonsterAI) scheduleSpawnAfterDeath(ctx context.Context, item monster.Monster, now time.Time) error {
	if item.SpawnID == "" {
		return nil
	}
	spawns, err := ai.monsters.ListSpawnPoints(ctx, item.MapID)
	if err != nil {
		return err
	}
	for _, spawn := range spawns {
		if spawn.ID != item.SpawnID {
			continue
		}
		spawn.NextSpawnAt = now.Add(service.RandomSpawnCooldown())
		spawn.UpdatedAt = now
		return ai.monsters.SaveSpawnPoint(ctx, spawn)
	}
	return nil
}

func (ai *MonsterAI) publish(eventType service.EventType, item monster.Monster, damage int) {
	if ai.events == nil {
		return
	}
	ai.events.Publish(service.Event{Type: eventType, ChunkID: world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)), Payload: service.MonsterPayload{Monster: item, Damage: damage}})
}

func manhattan(a, b world.Coord) int {
	x := a.X - b.X
	if x < 0 {
		x = -x
	}
	y := a.Y - b.Y
	if y < 0 {
		y = -y
	}
	return x + y
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
