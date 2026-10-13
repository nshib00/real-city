package simulation

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

type MonsterAI struct {
	monsters  service.MonsterRepository
	buildings service.BuildingRepository
	worlds    service.WorldRepository
	events    *service.EventBus
	log       *slog.Logger
}

func NewMonsterAI(monsters service.MonsterRepository, buildings service.BuildingRepository, worlds service.WorldRepository, events *service.EventBus, log *slog.Logger) *MonsterAI {
	return &MonsterAI{monsters: monsters, buildings: buildings, worlds: worlds, events: events, log: log}
}

func (ai *MonsterAI) Tick(ctx context.Context, now time.Time, limit int) (int, error) {
	items, err := ai.monsters.ListActiveForTick(ctx, service.DefaultWorldID, limit)
	if err != nil {
		return 0, err
	}
	chunkCache := make(map[world.ChunkCoord]world.Chunk)
	processed := 0
	for _, item := range items {
		if limit > 0 && processed >= limit {
			break
		}
		if !item.Alive() {
			continue
		}
		updated, eventType, targetID, err := ai.step(ctx, item, now, chunkCache)
		if err != nil {
			return processed, err
		}
		if updated.ID == "" {
			continue
		}
		if err := ai.monsters.Update(ctx, updated); err != nil {
			return processed, err
		}
		_ = ai.monsters.AddEvent(ctx, monster.Event{ID: fmt.Sprintf("monster_event_%s_%d", updated.ID, now.UnixNano()), MonsterID: updated.ID, Type: string(eventType), TargetID: targetID, Tile: updated.Tile, CreatedAt: now})
		ai.publish(eventType, updated)
		ai.log.Info("pve.monster.tick", "event", "pve.monster.tick", "monster_id", updated.ID, "monster_type", updated.Type, "state", updated.State, "target_id", targetID, "chunk_id", world.ChunkID(updated.MapID, world.ChunkForTile(updated.Tile)))
		processed++
	}
	return processed, nil
}

func (ai *MonsterAI) step(ctx context.Context, item monster.Monster, now time.Time, chunkCache map[world.ChunkCoord]world.Chunk) (monster.Monster, service.EventType, string, error) {
	target, ok, err := ai.nearestTarget(ctx, item)
	if err != nil {
		return monster.Monster{}, "", "", err
	}
	item.UpdatedAt = now
	if ok && item.DistanceTo(target.Tile) <= item.AggroRadius {
		item.State = monster.StateAggro
		item.TargetID = string(target.ID)
		item.TargetType = "building"
		if item.CanAttack(now, target.Tile) {
			item.State = monster.StateAttacking
			item.NextAttackAt = now.Add(item.AttackCooldown)
			return item, service.EventMonsterAttacked, string(target.ID), nil
		}
		next, err := ai.nextPassableStep(ctx, item.Tile, target.Tile, item.SpeedTiles, chunkCache)
		if err != nil {
			return monster.Monster{}, "", "", err
		}
		item.Tile = next
		item.LastMovedAt = now
		return item, service.EventMonsterMoved, string(target.ID), nil
	}
	if targetMonster, ok, err := ai.collidingMonster(ctx, item); err != nil {
		return monster.Monster{}, "", "", err
	} else if ok && item.CanAttack(now, targetMonster.Tile) {
		targetMonster.ApplyDamage(item.Damage, now)
		if err := ai.monsters.Update(ctx, targetMonster); err != nil {
			return monster.Monster{}, "", "", err
		}
		if targetMonster.State == monster.StateDead {
			if err := ai.createLootDrop(ctx, targetMonster, now); err != nil {
				return monster.Monster{}, "", "", err
			}
			if err := ai.scheduleSpawnAfterDeath(ctx, targetMonster, now); err != nil {
				return monster.Monster{}, "", "", err
			}
		}
		item.State = monster.StateAttacking
		item.TargetID = string(targetMonster.ID)
		item.TargetType = "monster"
		item.NextAttackAt = now.Add(item.AttackCooldown)
		return item, service.EventMonsterAttacked, string(targetMonster.ID), nil
	}
	item.State = monster.StateWandering
	item.TargetID = ""
	item.TargetType = ""
	wander := monster.WanderFrom(item.HomeTile, now.Unix()+int64(len(item.ID)), 5)
	if passable, err := ai.isPassable(ctx, wander, chunkCache); err != nil {
		return monster.Monster{}, "", "", err
	} else if passable {
		item.Tile = wander
	}
	item.LastMovedAt = now
	return item, service.EventMonsterMoved, "", nil
}

func (ai *MonsterAI) nearestTarget(ctx context.Context, item monster.Monster) (building.Building, bool, error) {
	chunk := world.ChunkForTile(item.Tile)
	buildings, err := ai.buildings.ListByChunk(ctx, item.MapID, chunk)
	if err != nil {
		return building.Building{}, false, err
	}
	var best building.Building
	bestDistance := 0
	for _, target := range buildings {
		if target.State == building.StateRuined || target.State == building.StatePlanned {
			continue
		}
		distance := item.DistanceTo(target.Tile)
		if best.ID == "" || distance < bestDistance {
			best = target
			bestDistance = distance
		}
	}
	return best, best.ID != "", nil
}

func (ai *MonsterAI) collidingMonster(ctx context.Context, item monster.Monster) (monster.Monster, bool, error) {
	items, err := ai.monsters.ListByViewport(ctx, item.MapID, item.Tile.X-1, item.Tile.Y-1, item.Tile.X+1, item.Tile.Y+1)
	if err != nil {
		return monster.Monster{}, false, err
	}
	var best monster.Monster
	bestDistance := 0
	for _, other := range items {
		if other.ID == item.ID || !other.Alive() {
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

func (ai *MonsterAI) nextPassableStep(ctx context.Context, from world.Coord, to world.Coord, speed int, chunkCache map[world.ChunkCoord]world.Chunk) (world.Coord, error) {
	next := from
	for step := 0; step < max(1, speed); step++ {
		candidates := []world.Coord{
			monster.StepToward(next, to, 1),
			{X: next.X + 1, Y: next.Y},
			{X: next.X - 1, Y: next.Y},
			{X: next.X, Y: next.Y + 1},
			{X: next.X, Y: next.Y - 1},
		}
		best := next
		bestDistance := manhattan(next, to)
		for _, candidate := range candidates {
			if candidate == next {
				continue
			}
			passable, err := ai.isPassable(ctx, candidate, chunkCache)
			if err != nil {
				return world.Coord{}, err
			}
			if !passable {
				continue
			}
			distance := manhattan(candidate, to)
			if best == next || distance < bestDistance {
				best = candidate
				bestDistance = distance
			}
		}
		if best == next {
			return next, nil
		}
		next = best
	}
	return next, nil
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
	for _, item := range chunk.Tiles {
		if item.Coord == tile {
			return item.Terrain == world.TerrainForest || item.Terrain == world.TerrainGrass, nil
		}
	}
	return false, nil
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

func (ai *MonsterAI) publish(eventType service.EventType, item monster.Monster) {
	if ai.events == nil {
		return
	}
	ai.events.Publish(service.Event{Type: eventType, ChunkID: world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)), Payload: service.MonsterPayload{Monster: item}})
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
