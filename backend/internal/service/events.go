package service

import (
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
	"real-city/backend/internal/domain/world"
)

type EventType string

const (
	EventTileChanged          EventType = "world.tile.changed"
	EventBuildingPlaced       EventType = "world.building.placed"
	EventBuildingUpdated      EventType = "world.building.updated"
	EventBuildingRemoved      EventType = "world.building.removed"
	EventResourceChanged      EventType = "world.resource.changed"
	EventProductionDone       EventType = "economy.production.completed"
	EventInventoryChanged     EventType = "economy.inventory.changed"
	EventPresenceChanged      EventType = "presence.changed"
	EventPresenceMoved        EventType = "presence.moved"
	EventCombatResolved       EventType = "combat.resolved"
	EventMonsterSpawned       EventType = "monster.spawned"
	EventMonsterMoved         EventType = "monster.moved"
	EventMonsterAttacked      EventType = "monster.attacked"
	EventMonsterDamaged       EventType = "monster.damaged"
	EventMonsterDied          EventType = "monster.died"
	EventMonsterDespawned     EventType = "monster.despawned"
	EventMonsterThreatWarning EventType = "monster.threat.warning"
	EventMonsterLootDropped   EventType = "monster.loot.dropped"
	EventMonsterLootClaimed   EventType = "monster.loot.claimed"
	EventCannonShot           EventType = "cannon.shot"
	EventDefenseTriggered     EventType = "defense.triggered"
	EventTowerThreatDetected  EventType = "tower.threat.detected"
	EventTowerThreatShared    EventType = "tower.threat.shared"
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
	Tile   world.Tile `json:"tile"`
	Reason string     `json:"reason,omitempty"`
}

type BuildingPayload struct {
	Building building.Building `json:"building"`
	Reason   string            `json:"reason,omitempty"`
	Damage   int               `json:"damage,omitempty"`
}

type BuildingRemovedPayload struct {
	BuildingID   building.ID   `json:"building_id"`
	Reason       string        `json:"reason,omitempty"`
	Damage       int           `json:"damage,omitempty"`
	TileX        int           `json:"tile_x,omitempty"`
	TileY        int           `json:"tile_y,omitempty"`
	BuildingType building.Type `json:"building_type,omitempty"`
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

type PresenceMovedPayload struct {
	Player player.Presence `json:"player"`
}

type MonsterPayload struct {
	Monster monster.Monster `json:"monster"`
	Damage  int             `json:"damage,omitempty"`
	Source  string          `json:"source,omitempty"`
}

type MonsterThreatWarningPayload struct {
	MonsterType string    `json:"monster_type"`
	TileX       int       `json:"tile_x"`
	TileY       int       `json:"tile_y"`
	ArrivesAt   time.Time `json:"arrives_at"`
}

type MonsterLootPayload struct {
	Loot monster.LootDrop `json:"loot"`
}

type CannonShotPayload struct {
	BuildingID   string `json:"building_id"`
	BuildingType string `json:"building_type,omitempty"`
	MonsterID    string `json:"monster_id"`
	Damage       int    `json:"damage"`
	DamageType   string `json:"damage_type"`
	Ammo         string `json:"ammo"`
	TileX        int    `json:"tile_x"`
	TileY        int    `json:"tile_y"`
	TargetTileX  int    `json:"target_tile_x"`
	TargetTileY  int    `json:"target_tile_y"`
}

type DefenseTriggeredPayload struct {
	BuildingID   string `json:"building_id"`
	BuildingType string `json:"building_type"`
	MonsterID    string `json:"monster_id"`
	TileX        int    `json:"tile_x"`
	TileY        int    `json:"tile_y"`
}

type TowerThreatPayload struct {
	IncidentID       string    `json:"incident_id,omitempty"`
	TowerID          string    `json:"tower_id"`
	MonsterID        string    `json:"monster_id"`
	MonsterType      string    `json:"monster_type"`
	TileX            int       `json:"tile_x"`
	TileY            int       `json:"tile_y"`
	TargetBuildingID string    `json:"target_building_id"`
	DetectedAt       time.Time `json:"detected_at"`
}

type TowerSharedThreatPayload = toweralert.SharedAlert

type ChatMessagePayload struct{ Message chat.Message }
