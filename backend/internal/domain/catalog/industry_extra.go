package catalog

import (
	"time"

	"real-city/backend/internal/domain/economy"
)

func init() {
	ProductionRecipes = append(ProductionRecipes,
		economy.ProductionRecipe{
			ID: "reinforced_concrete_batch", Name: "Железобетон", BuildingType: "concrete_plant",
			RequiredLevel: 6, Duration: 60 * time.Minute, Workers: 16, FuelPerRun: 18,
			Input:  []economy.ResourceAmount{{Resource: economy.ResourceConcrete, Amount: 12}, {Resource: economy.ResourceSteel, Amount: 3}},
			Output: []economy.ResourceAmount{{Resource: economy.ResourceReinforcedConc, Amount: 8}},
		},
		economy.ProductionRecipe{
			ID: "armor_plates_batch", Name: "Защитные пластины", BuildingType: "military_factory",
			RequiredLevel: 5, Duration: 65 * time.Minute, Workers: 14, FuelPerRun: 20,
			Input:  []economy.ResourceAmount{{Resource: economy.ResourceSteel, Amount: 8}, {Resource: economy.ResourceConcrete, Amount: 10}},
			Output: []economy.ResourceAmount{{Resource: economy.ResourceArmorPlates, Amount: 4}},
		},
		economy.ProductionRecipe{
			ID: "rune_tile_batch", Name: "Руническая черепица", BuildingType: "tile_factory",
			RequiredLevel: 8, Duration: 90 * time.Minute, Workers: 20,
			Input:  []economy.ResourceAmount{{Resource: economy.ResourceTile, Amount: 12}, {Resource: economy.ResourceQuietPowder, Amount: 1}, {Resource: economy.ResourceMemoryShard, Amount: 1}, {Resource: economy.ResourceCoal, Amount: 25}},
			Output: []economy.ResourceAmount{{Resource: economy.ResourceRuneTile, Amount: 1}},
		},
	)
}
