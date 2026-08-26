package dto

import (
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
)

type PlaceBuildingRequest struct {
	Type  string `json:"type"`
	TileX int    `json:"tile_x"`
	TileY int    `json:"tile_y"`
}

type PatchBuildingRequest struct {
	Action string `json:"action"`
}

type BuildingResponse struct {
	ID          string     `json:"id"`
	MapID       string     `json:"map_id"`
	OwnerID     string     `json:"owner_id"`
	Type        string     `json:"type"`
	Name        string     `json:"name"`
	Level       int        `json:"level"`
	State       string     `json:"state"`
	Health      int        `json:"health"`
	TileX       int        `json:"tile_x"`
	TileY       int        `json:"tile_y"`
	FootprintW  int        `json:"footprint_w"`
	FootprintH  int        `json:"footprint_h"`
	StartedAt   time.Time  `json:"started_at"`
	CompletesAt *time.Time `json:"completes_at"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
}

type BuildingCatalogResponse struct {
	Type              string         `json:"type"`
	Category          string         `json:"category"`
	Name              string         `json:"name"`
	Level             int            `json:"level"`
	FootprintW        int            `json:"footprint_w"`
	FootprintH        int            `json:"footprint_h"`
	BuildSeconds      int            `json:"build_seconds"`
	Population        int            `json:"population"`
	Cost              []BuildingCost `json:"cost"`
	RequiresTownHall  bool           `json:"requires_town_hall"`
	CountsTowardLimit bool           `json:"counts_toward_limit"`
	UpgradeTo         []string       `json:"upgrade_to"`
}

type BuildingCost struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}

func Building(b building.Building) BuildingResponse {
	return BuildingResponse{
		ID:          string(b.ID),
		MapID:       b.MapID,
		OwnerID:     string(b.OwnerID),
		Type:        string(b.Type),
		Name:        b.Name,
		Level:       b.Level,
		State:       string(b.State),
		Health:      b.Health,
		TileX:       b.Tile.X,
		TileY:       b.Tile.Y,
		FootprintW:  b.Footprint.Width,
		FootprintH:  b.Footprint.Height,
		StartedAt:   b.StartedAt,
		CompletesAt: b.CompletesAt,
		CreatedAt:   b.CreatedAt,
		UpdatedAt:   b.UpdatedAt,
	}
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
		responses = append(responses, BuildingCatalogResponse{
			Type:              string(item.Type),
			Category:          item.Category,
			Name:              item.Name,
			Level:             item.Level,
			FootprintW:        item.Footprint.Width,
			FootprintH:        item.Footprint.Height,
			BuildSeconds:      int(item.BuildDuration.Seconds()),
			Population:        item.Population,
			Cost:              cost,
			RequiresTownHall:  item.RequiresTownHall,
			CountsTowardLimit: item.CountsTowardLimit,
			UpgradeTo:         upgradeTo,
		})
	}
	return responses
}
