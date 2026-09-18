package economy

func FuelCostForRun(recipe ProductionRecipe) []ResourceAmount {
	if recipe.FuelPerRun <= 0 {
		return nil
	}
	return []ResourceAmount{{Resource: ResourceFuel, Amount: recipe.FuelPerRun}}
}

func WithFuelCost(input []ResourceAmount, recipe ProductionRecipe) []ResourceAmount {
	fuel := FuelCostForRun(recipe)
	if len(fuel) == 0 {
		return input
	}
	cost := append([]ResourceAmount(nil), input...)
	return append(cost, fuel...)
}
