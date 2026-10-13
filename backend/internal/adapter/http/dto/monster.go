package dto

import (
	"time"

	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/service"
)

type MonsterResponse struct {
	ID          string    `json:"id"`
	Type        string    `json:"type"`
	State       string    `json:"state"`
	TileX       int       `json:"tile_x"`
	TileY       int       `json:"tile_y"`
	TargetID    string    `json:"target_id"`
	TargetType  string    `json:"target_type"`
	Health      int       `json:"health"`
	MaxHealth   int       `json:"max_health"`
	Damage      int       `json:"damage"`
	AggroRadius int       `json:"aggro_radius"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type MonsterSpecResponse struct {
	Type        string `json:"type"`
	Name        string `json:"name"`
	MaxHealth   int    `json:"max_health"`
	Damage      int    `json:"damage"`
	SpeedTiles  int    `json:"speed_tiles"`
	AggroRadius int    `json:"aggro_radius"`
	AttackRange int    `json:"attack_range"`
	LootCoins   int    `json:"loot_coins"`
	SpawnWeight int    `json:"spawn_weight"`
}

type ThreatResponse struct {
	TileX      int      `json:"tile_x"`
	TileY      int      `json:"tile_y"`
	Level      int      `json:"level"`
	MonsterIDs []string `json:"monster_ids"`
}

type LootDropResponse struct {
	ID        string           `json:"id"`
	MonsterID string           `json:"monster_id"`
	TileX     int              `json:"tile_x"`
	TileY     int              `json:"tile_y"`
	Items     []ResourceAmount `json:"items"`
	CreatedAt time.Time        `json:"created_at"`
}

type MonsterAttackResponse struct {
	Monster MonsterResponse  `json:"monster"`
	Rewards []service.Reward `json:"rewards"`
}

func Monster(item monster.Monster) MonsterResponse {
	return MonsterResponse{
		ID: string(item.ID), Type: string(item.Type), State: string(item.State), TileX: item.Tile.X, TileY: item.Tile.Y,
		TargetID: item.TargetID, TargetType: item.TargetType, Health: item.Health, MaxHealth: item.MaxHealth,
		Damage: item.Damage, AggroRadius: item.AggroRadius, UpdatedAt: item.UpdatedAt,
	}
}

func Monsters(items []monster.Monster) []MonsterResponse {
	responses := make([]MonsterResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, Monster(item))
	}
	return responses
}

func MonsterSpec(item monster.Spec) MonsterSpecResponse {
	return MonsterSpecResponse{
		Type: string(item.Type), Name: item.Name, MaxHealth: item.MaxHealth, Damage: item.Damage,
		SpeedTiles: item.SpeedTiles, AggroRadius: item.AggroRadius, AttackRange: item.AttackRange, LootCoins: item.LootCoins, SpawnWeight: item.SpawnWeight,
	}
}

func MonsterSpecs(items []monster.Spec) []MonsterSpecResponse {
	responses := make([]MonsterSpecResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, MonsterSpec(item))
	}
	return responses
}

func Threats(items []monster.Threat) []ThreatResponse {
	responses := make([]ThreatResponse, 0, len(items))
	for _, item := range items {
		ids := make([]string, 0, len(item.MonsterIDs))
		for _, id := range item.MonsterIDs {
			ids = append(ids, string(id))
		}
		responses = append(responses, ThreatResponse{TileX: item.Tile.X, TileY: item.Tile.Y, Level: item.Level, MonsterIDs: ids})
	}
	return responses
}

func LootDrop(item monster.LootDrop) LootDropResponse {
	return LootDropResponse{
		ID:        string(item.ID),
		MonsterID: string(item.MonsterID),
		TileX:     item.Tile.X,
		TileY:     item.Tile.Y,
		Items:     resourceAmounts(item.Items),
		CreatedAt: item.CreatedAt,
	}
}

func LootDrops(items []monster.LootDrop) []LootDropResponse {
	responses := make([]LootDropResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, LootDrop(item))
	}
	return responses
}
