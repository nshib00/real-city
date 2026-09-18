package service

import (
	"context"

	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
)

type ThreatService struct {
	monsters MonsterRepository
}

func NewThreatService(monsters MonsterRepository) *ThreatService {
	return &ThreatService{monsters: monsters}
}

func (s *ThreatService) Around(ctx context.Context, center world.Coord, radius int) ([]monster.Threat, error) {
	if radius <= 0 {
		radius = 24
	}
	items, err := s.monsters.ListByViewport(ctx, DefaultWorldID, center.X-radius, center.Y-radius, center.X+radius, center.Y+radius)
	if err != nil {
		return nil, err
	}
	byTile := make(map[world.Coord]monster.Threat)
	for _, item := range items {
		level := item.Damage + item.MaxHealth/20
		threat := byTile[item.Tile]
		threat.Tile = item.Tile
		threat.Level += level
		threat.MonsterIDs = append(threat.MonsterIDs, item.ID)
		byTile[item.Tile] = threat
	}
	result := make([]monster.Threat, 0, len(byTile))
	for _, item := range byTile {
		result = append(result, item)
	}
	return result, nil
}
