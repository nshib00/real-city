package dto

import (
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

type ResourceAmount struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}

type InventoryResponse struct {
	PlayerID     string           `json:"player_id"`
	Items        []ResourceAmount `json:"items"`
	CoinCapacity int              `json:"coin_capacity"`
	UpdatedAt    time.Time        `json:"updated_at"`
}

type TransactionResponse struct {
	ID        string    `json:"id"`
	Kind      string    `json:"kind"`
	Resource  string    `json:"resource"`
	Amount    int       `json:"amount"`
	Reason    string    `json:"reason"`
	CreatedAt time.Time `json:"created_at"`
}

type ResourceNodeResponse struct {
	ID        string     `json:"id"`
	Type      string     `json:"type"`
	Resource  string     `json:"resource"`
	Amount    int        `json:"amount"`
	MaxAmount int        `json:"max_amount"`
	State     string     `json:"state"`
	OwnerID   string     `json:"owner_id"`
	TileX     int        `json:"tile_x"`
	TileY     int        `json:"tile_y"`
	RespawnAt *time.Time `json:"respawn_at"`
}

type ProductionRecipeResponse struct {
	ID           string           `json:"id"`
	Name         string           `json:"name"`
	BuildingType string           `json:"building_type"`
	DurationSec  int              `json:"duration_sec"`
	Workers      int              `json:"workers"`
	Input        []ResourceAmount `json:"input"`
	Output       []ResourceAmount `json:"output"`
}

type ProductionJobResponse struct {
	ID          string    `json:"id"`
	BuildingID  string    `json:"building_id"`
	RecipeID    string    `json:"recipe_id"`
	State       string    `json:"state"`
	StartedAt   time.Time `json:"started_at"`
	CompletesAt time.Time `json:"completes_at"`
}

type StartProductionRequest struct {
	BuildingID string `json:"building_id"`
	RecipeID   string `json:"recipe_id"`
}

type PatchProductionRequest struct {
	Action string `json:"action"`
}

type PatchResourceNodeRequest struct {
	Action string `json:"action"`
}

type HarvestFieldRequest struct {
	Super bool `json:"super"`
}

type PopulationResponse struct {
	Total      int `json:"total"`
	Free       int `json:"free"`
	Builders   int `json:"builders"`
	Production int `json:"production"`
	Fields     int `json:"fields"`
	Defense    int `json:"defense"`
	Repair     int `json:"repair"`
}

func Inventory(item economy.Inventory) InventoryResponse {
	items := make([]ResourceAmount, 0, len(item.Items))
	for resource, amount := range item.Items {
		items = append(items, ResourceAmount{Resource: string(resource), Amount: amount})
	}
	return InventoryResponse{PlayerID: item.PlayerID, Items: items, CoinCapacity: item.CoinCapacity, UpdatedAt: item.UpdatedAt}
}

func Transactions(items []economy.Transaction) []TransactionResponse {
	responses := make([]TransactionResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, TransactionResponse{
			ID:        string(item.ID),
			Kind:      string(item.Kind),
			Resource:  string(item.Resource),
			Amount:    item.Amount,
			Reason:    item.Reason,
			CreatedAt: item.CreatedAt,
		})
	}
	return responses
}

func ResourceNode(item economy.ResourceNode) ResourceNodeResponse {
	return ResourceNodeResponse{
		ID:        string(item.ID),
		Type:      item.Type,
		Resource:  string(item.Resource),
		Amount:    item.Amount,
		MaxAmount: item.MaxAmount,
		State:     string(item.State),
		OwnerID:   item.OwnerID,
		TileX:     item.Tile.X,
		TileY:     item.Tile.Y,
		RespawnAt: item.RespawnAt,
	}
}

func ResourceNodes(items []economy.ResourceNode) []ResourceNodeResponse {
	responses := make([]ResourceNodeResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, ResourceNode(item))
	}
	return responses
}

func ProductionRecipe(item economy.ProductionRecipe) ProductionRecipeResponse {
	return ProductionRecipeResponse{
		ID:           item.ID,
		Name:         item.Name,
		BuildingType: item.BuildingType,
		DurationSec:  int(item.Duration.Seconds()),
		Workers:      item.Workers,
		Input:        resourceAmounts(item.Input),
		Output:       resourceAmounts(item.Output),
	}
}

func ProductionRecipes(items []economy.ProductionRecipe) []ProductionRecipeResponse {
	responses := make([]ProductionRecipeResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, ProductionRecipe(item))
	}
	return responses
}

func ProductionJob(item economy.ProductionJob) ProductionJobResponse {
	return ProductionJobResponse{
		ID:          string(item.ID),
		BuildingID:  item.BuildingID,
		RecipeID:    item.RecipeID,
		State:       string(item.State),
		StartedAt:   item.StartedAt,
		CompletesAt: item.CompletesAt,
	}
}

func ProductionJobs(items []economy.ProductionJob) []ProductionJobResponse {
	responses := make([]ProductionJobResponse, 0, len(items))
	for _, item := range items {
		responses = append(responses, ProductionJob(item))
	}
	return responses
}

func Population(item player.Population) PopulationResponse {
	return PopulationResponse{
		Total:      item.Total,
		Free:       item.Free,
		Builders:   item.Builders,
		Production: item.Production,
		Fields:     item.Fields,
		Defense:    item.Defense,
		Repair:     item.Repair,
	}
}

func resourceAmounts(items []economy.ResourceAmount) []ResourceAmount {
	result := make([]ResourceAmount, 0, len(items))
	for _, item := range items {
		result = append(result, ResourceAmount{Resource: string(item.Resource), Amount: item.Amount})
	}
	return result
}
