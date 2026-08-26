package catalog

import "real-city/backend/internal/domain/economy"

func ProductionCatalog() []economy.ProductionRecipe {
	return append([]economy.ProductionRecipe(nil), ProductionRecipes...)
}
