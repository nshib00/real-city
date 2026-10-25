package catalog

import (
	"time"

	"real-city/backend/internal/domain/economy"
)

const OilExtractionRecipeID = "oil_extraction"

func OilExtractionRecipe(level int) economy.ProductionRecipe {
	recipe := economy.ProductionRecipe{
		ID: OilExtractionRecipeID, Name: "Добыча нефти", BuildingType: "oil_well",
		RequiredLevel: level,
	}
	switch level {
	case 2:
		recipe.Duration, recipe.Workers = 25*time.Minute, 21
		recipe.Output = []economy.ResourceAmount{{Resource: economy.ResourceOil, Amount: 250}}
		recipe.RareOutput = []economy.RareProductionOutput{{Resource: economy.ResourceAmberEssence, Amount: 1, Chance: 0.01}}
	case 3:
		recipe.Duration, recipe.Workers = time.Hour, 27
		recipe.Output = []economy.ResourceAmount{{Resource: economy.ResourceOil, Amount: 400}}
		recipe.RareOutput = []economy.RareProductionOutput{
			{Resource: economy.ResourceAmberEssence, Amount: 1, Chance: 0.02},
			{Resource: economy.ResourceQuietPowder, Amount: 1, Chance: 0.005},
		}
	default:
		recipe.RequiredLevel, recipe.Duration, recipe.Workers = 1, 30*time.Minute, 15
		recipe.Output = []economy.ResourceAmount{{Resource: economy.ResourceOil, Amount: 100}}
	}
	return recipe
}

func OilExtractionDepletion(level int) int {
	switch level {
	case 2:
		return 225
	case 3:
		return 320
	default:
		return 100
	}
}
