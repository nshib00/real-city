package service

import (
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

type EventType string

const (
	EventTileChanged      EventType = "world.tile.changed"
	EventBuildingPlaced   EventType = "world.building.placed"
	EventBuildingUpdated  EventType = "world.building.updated"
	EventBuildingRemoved  EventType = "world.building.removed"
	EventResourceChanged  EventType = "world.resource.changed"
	EventProductionDone   EventType = "economy.production.completed"
	EventInventoryChanged EventType = "economy.inventory.changed"
	EventPresenceChanged  EventType = "presence.changed"
	EventCombatResolved   EventType = "combat.resolved"
	EventMonsterSpawned   EventType = "monster.spawned"
	EventMonsterMoved     EventType = "monster.moved"
	EventMonsterAttacked  EventType = "monster.attacked"
	EventMonsterDamaged   EventType = "monster.damaged"
	EventMonsterDied      EventType = "monster.died"
	EventMonsterDespawned EventType = "monster.despawned"
)

type Event struct {
	Type      EventType
	ChunkID   string
	PlayerID  player.ID
	Alliance  string
	Payload   any
	CreatedAt time.Time
}

type TileChangedPayload struct {
	Tile world.Tile `json:"tile"`
}

type BuildingPayload struct {
	Building building.Building `json:"building"`
}

type BuildingRemovedPayload struct {
	BuildingID building.ID `json:"building_id"`
}

type ResourceChangedPayload struct {
	Node economy.ResourceNode `json:"node"`
}

type ProductionPayload struct {
	Job       economy.ProductionJob `json:"job"`
	Inventory economy.Inventory     `json:"inventory"`
}

type InventoryPayload struct {
	Inventory economy.Inventory `json:"inventory"`
}

type PresencePayload struct {
	PlayerID player.ID `json:"player_id"`
	Online   bool      `json:"online"`
}

type MonsterPayload struct {
	Monster monster.Monster `json:"monster"`
}
