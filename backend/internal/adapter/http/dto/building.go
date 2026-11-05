package dto

import (
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
)

type PlaceBuildingRequest struct {
	Type  string `json:"type"`
	TileX int    `json:"tile_x"`
	TileY int    `json:"tile_y"`
}

type PatchBuildingRequest struct {
	Action     string `json:"action"`
	TargetType string `json:"target_type,omitempty"`
	TileX      *int   `json:"tile_x,omitempty"`
	TileY      *int   `json:"tile_y,omitempty"`
	Rotation   *int   `json:"rotation,omitempty"`
}

type RushCompletionResponse struct {
	CrystalCost int `json:"crystal_cost"`
}

type BuildingResponse struct {
	ID                       string     `json:"id"`
	MapID                    string     `json:"map_id"`
	OwnerID                  string     `json:"owner_id"`
	Type                     string     `json:"type"`
	Name                     string     `json:"name"`
	Level                    int        `json:"level"`
	State                    string     `json:"state"`
	Health                   int        `json:"health"`
	MaxHealth                int        `json:"max_health"`
	DemolitionRefundCoins    int        `json:"demolition_refund_coins"`
	TileX                    int        `json:"tile_x"`
	TileY                    int        `json:"tile_y"`
	Rotation                 int        `json:"rotation"`
	FootprintW               int        `json:"footprint_w"`
	FootprintH               int        `json:"footprint_h"`
	StartedAt                time.Time  `json:"started_at"`
	CompletesAt              *time.Time `json:"completes_at"`
	FieldStage               int        `json:"field_stage,omitempty"`
	GrowthStage              int        `json:"growth_stage,omitempty"`
	CropStage                int        `json:"crop_stage,omitempty"`
	SuperStage               int        `json:"super_stage,omitempty"`
	FieldStageStartedAt      *time.Time `json:"field_stage_started_at,omitempty"`
	FieldStageReadyAt        *time.Time `json:"field_stage_ready_at,omitempty"`
	FieldStageReady          bool       `json:"field_stage_ready,omitempty"`
	IsSuperCrop              bool       `json:"is_super_crop,omitempty"`
	SuperCrop                bool       `json:"super_crop,omitempty"`
	CreatedAt                time.Time  `json:"created_at"`
	UpdatedAt                time.Time  `json:"updated_at"`
	CannonEnabled            bool       `json:"cannon_enabled,omitempty"`
	TowerWatchkeeperAssigned bool       `json:"tower_watchkeeper_assigned"`
	CannonNextAttackAt       *time.Time `json:"cannon_next_attack_at,omitempty"`
	CannonTargetID           string     `json:"cannon_target_id,omitempty"`
	CannonRange              int        `json:"cannon_range,omitempty"`
	CannonDamage             int        `json:"cannon_damage,omitempty"`
	CannonAmmo               string     `json:"cannon_ammo,omitempty"`
	CannonCooldownSeconds    int        `json:"cannon_cooldown_seconds,omitempty"`
	CannonDamageType         string     `json:"cannon_damage_type,omitempty"`
	TrapCharges              int        `json:"trap_charges"`
	TrapMaxCharges           int        `json:"trap_max_charges,omitempty"`
	TrapDamage               int        `json:"trap_damage,omitempty"`
	DefenseSlots             int        `json:"defense_slots,omitempty"`
	DefensePatrolRadius      int        `json:"defense_patrol_radius,omitempty"`
	DefenseStaffRole         string     `json:"defense_staff_role,omitempty"`
}

type BuildingCatalogResponse struct {
	Type              string                 `json:"type"`
	Category          string                 `json:"category"`
	Name              string                 `json:"name"`
	Level             int                    `json:"level"`
	FootprintW        int                    `json:"footprint_w"`
	FootprintH        int                    `json:"footprint_h"`
	BuildSeconds      int                    `json:"build_seconds"`
	Population        int                    `json:"population"`
	Health            int                    `json:"health"`
	Cost              []BuildingCost         `json:"cost"`
	FirstLevel        bool                   `json:"first_level"`
	UpgradeLevels     []BuildingCatalogLevel `json:"upgrade_levels"`
	RequiresTownHall  bool                   `json:"requires_town_hall"`
	CountsTowardLimit bool                   `json:"counts_toward_limit"`
	UpgradeTo         []string               `json:"upgrade_to"`
}

type BuildingCatalogLevel struct {
	Level        int            `json:"level"`
	BuildSeconds int            `json:"build_seconds"`
	Population   int            `json:"population"`
	Health       int            `json:"health"`
	Cost         []BuildingCost `json:"cost"`
	NextType     string         `json:"next_type,omitempty"`
}

type BuildingCost struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}

func Building(b building.Building) BuildingResponse {
	response := BuildingResponse{
		ID:                       string(b.ID),
		MapID:                    b.MapID,
		OwnerID:                  string(b.OwnerID),
		Type:                     string(b.Type),
		Name:                     b.Name,
		Level:                    b.Level,
		State:                    string(b.State),
		Health:                   b.Health,
		MaxHealth:                maxHealth(b),
		DemolitionRefundCoins:    catalog.DemolitionRefundCoins(b.Type, b.Level),
		TileX:                    b.Tile.X,
		TileY:                    b.Tile.Y,
		Rotation:                 b.Rotation,
		FootprintW:               b.Footprint.Width,
		FootprintH:               b.Footprint.Height,
		StartedAt:                b.StartedAt,
		CompletesAt:              b.CompletesAt,
		CreatedAt:                b.CreatedAt,
		UpdatedAt:                b.UpdatedAt,
		CannonEnabled:            b.CannonEnabled,
		TowerWatchkeeperAssigned: b.TowerWatchkeeperAssigned,
		CannonNextAttackAt:       b.CannonNextAttackAt,
		CannonTargetID:           b.CannonTargetID,
		TrapCharges:              b.TrapCharges,
	}
	if catalog.IsDefenseWeapon(b.Type) {
		if stats, ok := catalog.DefenseWeaponLevel(b.Type, b.Level); ok {
			response.CannonRange = stats.Range
			response.CannonDamage = stats.Damage
			response.CannonAmmo = string(stats.Ammo)
			response.CannonCooldownSeconds = int(stats.Cooldown.Seconds())
			response.CannonDamageType = stats.DamageType
		}
	}
	if stats, ok := catalog.DefenseTrapLevel(b.Type, b.Level); ok {
		response.TrapMaxCharges = stats.MaxCharges
		response.TrapDamage = stats.Damage
	}
	if stats, ok := catalog.DefenseBaseLevel(b.Type, b.Level); ok {
		response.DefenseSlots = stats.Slots
		response.DefensePatrolRadius = stats.PatrolRadius
		response.DefenseStaffRole = stats.StaffRole
	}
	if economy.IsFieldCropBuildingType(string(b.Type)) && b.FieldStage > 0 {
		ready := b.FieldStageReadyAt != nil && !b.FieldStageReadyAt.After(time.Now().UTC())
		response.FieldStage = b.FieldStage
		response.GrowthStage = b.FieldStage
		response.CropStage = b.FieldStage
		response.FieldStageStartedAt = b.FieldStageStartedAt
		response.FieldStageReadyAt = b.FieldStageReadyAt
		response.FieldStageReady = ready
		response.IsSuperCrop = b.FieldSuperCrop
		response.SuperCrop = b.FieldSuperCrop
		if b.FieldSuperCrop {
			response.SuperStage = b.FieldStage
		}
	}
	return response
}

func maxHealth(b building.Building) int {
	spec, ok := catalog.GetBuilding(b.Type)
	if !ok {
		return 100
	}
	for _, level := range spec.UpgradeLevels {
		if level.Level == b.Level && level.Health > 0 {
			return level.Health
		}
	}
	if spec.Health > 0 {
		return spec.Health
	}
	return 100
}

func Buildings(items []building.Building) []BuildingResponse {
	responses := make([]BuildingResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, Building(item))
	}
	return responses
}

func BuildingCatalog(items []catalog.BuildingType) []BuildingCatalogResponse {
	responses := make([]BuildingCatalogResponse, 0, len(items))
	for _, item := range items {
		cost := make([]BuildingCost, 0, len(item.Cost))
		for _, c := range item.Cost {
			cost = append(cost, BuildingCost{Resource: c.Resource, Amount: c.Amount})
		}
		upgradeTo := make([]string, 0, len(item.UpgradeTo))
		for _, next := range item.UpgradeTo {
			upgradeTo = append(upgradeTo, string(next))
		}
		levels := make([]BuildingCatalogLevel, 0, max(1, len(item.UpgradeLevels)))
		if len(item.UpgradeLevels) == 0 {
			levels = append(levels, BuildingCatalogLevel{Level: item.Level, BuildSeconds: int(item.BuildDuration.Seconds()), Population: item.Population, Health: item.Health, Cost: cost})
		} else {
			for _, level := range item.UpgradeLevels {
				levelCost := make([]BuildingCost, 0, len(level.Cost))
				for _, c := range level.Cost {
					levelCost = append(levelCost, BuildingCost{Resource: c.Resource, Amount: c.Amount})
				}
				levels = append(levels, BuildingCatalogLevel{Level: level.Level, BuildSeconds: int(level.BuildDuration.Seconds()), Population: level.Population,
					Health: level.Health, Cost: levelCost, NextType: string(level.NextType)})
			}
		}
		responses = append(responses, BuildingCatalogResponse{
			Type:              string(item.Type),
			Category:          item.Category,
			Name:              item.Name,
			Level:             item.Level,
			FootprintW:        item.Footprint.Width,
			FootprintH:        item.Footprint.Height,
			BuildSeconds:      int(item.BuildDuration.Seconds()),
			Population:        item.Population,
			Health:            item.Health,
			Cost:              cost,
			FirstLevel:        catalog.CanPlaceDirectly(item.Type),
			UpgradeLevels:     levels,
			RequiresTownHall:  item.RequiresTownHall,
			CountsTowardLimit: item.CountsTowardLimit,
			UpgradeTo:         upgradeTo,
		})
	}
	return responses
}
