package service

import (
	"context"
	"log/slog"

	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
)

type CombatService struct {
	monsters *MonsterService
	log      *slog.Logger
}

func NewCombatService(monsters *MonsterService, log *slog.Logger) *CombatService {
	return &CombatService{monsters: monsters, log: log}
}

func (s *CombatService) AttackMonster(ctx context.Context, id monster.ID, playerID player.ID) (monster.Monster, []Reward, error) {
	item, rewards, err := s.monsters.Attack(ctx, id, playerID)
	if err == nil {
		s.log.Info("pve.combat.resolved", "event", "pve.combat.resolved", "monster_id", item.ID, "monster_type", item.Type, "player_id", playerID)
	}
	return item, rewards, err
}
