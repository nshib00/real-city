package dto

import (
	"testing"

	"real-city/backend/internal/domain/catalog"
)

func TestLumberYardRecipeResponseIncludesFuelAndRareChance(t *testing.T) {
	recipe, _ := catalog.RecipeForBuildingLevel("planks_from_wood", 4)
	response := ProductionRecipe(recipe)
	if response.RequiredLevel != 4 || response.DurationSec != 1395 || len(response.Input) != 2 || response.Input[0].Resource != "wood" || response.Input[0].Amount != 24 || response.Input[1].Resource != "fuel" || response.Input[1].Amount != 5 {
		t.Fatalf("unexpected sawmill recipe response: %#v", response)
	}
	if len(response.RareOutput) != 1 || response.RareOutput[0].Resource != "premium_planks" || response.RareOutput[0].Chance != 0.01 {
		t.Fatalf("unexpected rare output: %#v", response.RareOutput)
	}
}
