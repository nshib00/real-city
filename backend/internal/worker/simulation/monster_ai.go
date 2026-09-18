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
	events    *service.EventBus
	log       *slog.Logger
}

func NewMonsterAI(monsters service.MonsterRepository, buildings service.BuildingRepository, events *service.EventBus, log *slog.Logger) *MonsterAI {
	return &MonsterAI{monsters: monsters, buildings: buildings, events: events, log: log}
}

func (ai *MonsterAI) Tick(ctx context.Context, now time.Time, limit int) (int, error) {
	items, err := ai.monsters.ListByMap(ctx, service.DefaultWorldID)
	if err != nil {
		return 0, err
	}
	processed := 0
	for _, item := range items {
		if limit > 0 && processed >= limit {
			break
		}
		updated, eventType, targetID, err := ai.step(ctx, item, now)
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

func (ai *MonsterAI) step(ctx context.Context, item monster.Monster, now time.Time) (monster.Monster, service.EventType, string, error) {
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
		item.Tile = monster.StepToward(item.Tile, target.Tile, item.SpeedTiles)
		item.LastMovedAt = now
		return item, service.EventMonsterMoved, string(target.ID), nil
	}
	item.State = monster.StateWandering
	item.TargetID = ""
	item.TargetType = ""
	item.Tile = monster.WanderFrom(item.HomeTile, now.Unix()+int64(len(item.ID)), 5)
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

func (ai *MonsterAI) publish(eventType service.EventType, item monster.Monster) {
	if ai.events == nil {
		return
	}
	ai.events.Publish(service.Event{Type: eventType, ChunkID: world.ChunkID(item.MapID, world.ChunkForTile(item.Tile)), Payload: service.MonsterPayload{Monster: item}})
}
