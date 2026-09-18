package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type MonsterService struct {
	repo   MonsterRepository
	log    *slog.Logger
	events *EventBus
	now    func() time.Time
}

func NewMonsterService(repo MonsterRepository, log *slog.Logger) *MonsterService {
	return &MonsterService{repo: repo, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *MonsterService) SetEventBus(events *EventBus) {
	s.events = events
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
	if killed && item.LootCoins > 0 {
		rewards = []Reward{{Resource: "coins", Amount: item.LootCoins}}
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
	spec, ok := catalog.MonsterSpec(spawn.Type)
	if !ok {
		return monster.Monster{}, apperror.New(apperror.Validation, "unknown monster type")
	}
	item := monster.Monster{
		ID: monster.ID(fmt.Sprintf("monster_%s_%d", spawn.ID, now.UnixNano())), MapID: spawn.MapID, Type: spec.Type, State: monster.StateWandering,
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

type Reward struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}
