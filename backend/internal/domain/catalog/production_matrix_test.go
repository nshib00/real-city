package catalog

import (
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"testing"
	"time"
)

func TestMineAndRopeRecipesCoverActualLevels(t *testing.T) {
	for id, levels := range map[string]int{"mine_run": 12, "rope_yard_run": 8} {
		if IndustryRecipeLevels(id) != levels || !IsIndustryLevelRecipe(id) {
			t.Fatal(id, "missing levels")
		}
		for level := 1; level <= levels; level++ {
			r, ok := RecipeForBuildingLevel(id, level)
			if !ok || r.RequiredLevel != level || r.Workers <= 0 || r.Duration <= 0 || len(r.Output) == 0 {
				t.Fatal(id, level, r)
			}
			if ExperienceForBuilding(building.Type(r.BuildingType), level).Work <= 0 {
				t.Fatal("missing work XP", id, level)
			}
		}
	}
	r, _ := RecipeForBuildingLevel("mine_run", 1)
	if r.Duration != 330*time.Second || r.FuelPerRun != 0 || r.Output[0].Amount != 5 {
		t.Fatal(r)
	}
	r, _ = RecipeForBuildingLevel("mine_run", 12)
	if r.FuelPerRun != 47 || len(r.Input) != 1 || r.Input[0].Resource != economy.ResourceExplosives || r.Input[0].Amount != 2 {
		t.Fatal(r)
	}
	r, _ = RecipeForBuildingLevel("rope_yard_run", 8)
	if r.Input[0].Amount != 150 || r.Output[0].Amount != 55 || r.RareOutput[0].Chance != .04 {
		t.Fatal(r)
	}
}
