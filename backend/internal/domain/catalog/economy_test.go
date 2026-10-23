package catalog

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/economy"
)

func TestLumberYardRecipesMatchSpecification(t *testing.T) {
	cases := []struct {
		wood, planks, fuel, seconds int
		chance                      float64
	}{
		{15, 2, 0, 270, 0},
		{13, 4, 0, 490, 0},
		{19, 7, 0, 765, 0.005},
		{24, 11, 5, 1395, 0.01},
		{30, 15, 8, 1770, 0.017},
		{35, 20, 13, 2040, 0.026},
		{40, 25, 17, 2230, 0.037},
		{44, 33, 20, 2420, 0.053},
		{50, 37, 25, 2575, 0.062},
		{53, 40, 34, 2700, 0.075},
		{55, 44, 40, 2855, 0.096},
		{58, 54, 47, 3100, 0.135},
		{65, 65, 55, 3185, 0.172},
	}
	for index, want := range cases {
		level := index + 1
		recipe, ok := RecipeForBuildingLevel("planks_from_wood", level)
		if !ok || recipe.RequiredLevel != level || recipe.Duration != time.Duration(want.seconds)*time.Second || recipe.FuelPerRun != want.fuel {
			t.Fatalf("unexpected level %d recipe: %#v", level, recipe)
		}
		assertInput(t, recipe.Input, economy.ResourceWood, want.wood)
		assertOutput(t, recipe.Output, economy.ResourcePlanks, want.planks)
		if want.chance == 0 {
			if len(recipe.RareOutput) != 0 {
				t.Fatalf("level %d should not produce premium planks", level)
			}
		} else if len(recipe.RareOutput) != 1 || recipe.RareOutput[0].Resource != economy.ResourcePremiumPlanks || recipe.RareOutput[0].Amount != 1 || recipe.RareOutput[0].Chance != want.chance {
			t.Fatalf("unexpected level %d rare output: %#v", level, recipe.RareOutput)
		}
	}
}

func TestSandQuarryRecipeForBuildingLevel(t *testing.T) {
	levelOne, ok := RecipeForBuildingLevel("sand_quarry_run", 1)
	if !ok {
		t.Fatal("sand quarry recipe not found")
	}
	if levelOne.Duration != 8*time.Minute+50*time.Second || levelOne.Workers != 4 {
		t.Fatalf("unexpected level 1 sand quarry recipe: %#v", levelOne)
	}
	assertOutput(t, levelOne.Output, economy.ResourceSand, 10)
	assertOutput(t, levelOne.Output, economy.ResourceCoins, 70)
	if len(levelOne.RareOutput) != 0 {
		t.Fatalf("level 1 should not have rare output: %#v", levelOne.RareOutput)
	}

	levelThree, _ := RecipeForBuildingLevel("sand_quarry_run", 3)
	if levelThree.Duration != 10*time.Minute+15*time.Second || levelThree.Workers != 7 {
		t.Fatalf("unexpected level 3 sand quarry recipe: %#v", levelThree)
	}
	assertOutput(t, levelThree.Output, economy.ResourceSand, 26)
	if len(levelThree.RareOutput) != 1 || levelThree.RareOutput[0].Resource != economy.ResourceBlueSalt || levelThree.RareOutput[0].Chance != 0.012 {
		t.Fatalf("unexpected level 3 rare output: %#v", levelThree.RareOutput)
	}

	levelEleven, _ := RecipeForBuildingLevel("sand_quarry_run", 99)
	if levelEleven.RequiredLevel != 11 || levelEleven.Duration != 46*time.Minute+50*time.Second || levelEleven.Workers != 23 {
		t.Fatalf("unexpected clamped level 11 sand quarry recipe: %#v", levelEleven)
	}
	assertOutput(t, levelEleven.Output, economy.ResourceSand, 114)
	assertOutput(t, levelEleven.Output, economy.ResourceCoins, 19300)
	if len(levelEleven.RareOutput) != 1 || levelEleven.RareOutput[0].Chance != 0.174 {
		t.Fatalf("unexpected level 11 rare output: %#v", levelEleven.RareOutput)
	}
}

func TestClayQuarryRecipesMatchSpecification(t *testing.T) {
	cases := []struct {
		clay, fuel, workers, seconds int
		chance                     float64
	}{
		{18, 0, 3, 360, 0},
		{30, 0, 4, 450, 0},
		{44, 0, 5, 560, 0.008},
		{62, 0, 7, 760, 0.016},
		{84, 0, 9, 970, 0.029},
		{112, 0, 11, 1200, 0.044},
		{150, 8, 13, 1410, 0.065},
		{188, 12, 15, 1640, 0.088},
		{230, 17, 17, 1905, 0.114},
		{276, 23, 19, 2190, 0.142},
		{330, 30, 21, 2520, 0.175},
		{395, 38, 24, 2880, 0.22},
	}
	for index, want := range cases {
		level := index + 1
		recipe, ok := RecipeForBuildingLevel("clay_quarry_run", level)
		if !ok || recipe.RequiredLevel != level || recipe.Duration != time.Duration(want.seconds)*time.Second || recipe.Workers != want.workers || recipe.FuelPerRun != want.fuel {
			t.Fatalf("unexpected level %d recipe: %#v", level, recipe)
		}
		assertOutput(t, recipe.Output, economy.ResourceClay, want.clay)
		if want.chance == 0 {
			if len(recipe.RareOutput) != 0 {
				t.Fatalf("level %d should not produce kaolin: %#v", level, recipe.RareOutput)
			}
		} else if len(recipe.RareOutput) != 1 || recipe.RareOutput[0].Resource != economy.ResourceKaolin || recipe.RareOutput[0].Amount != 1 || recipe.RareOutput[0].Chance != want.chance {
			t.Fatalf("unexpected level %d rare output: %#v", level, recipe.RareOutput)
		}
	}
	last, _ := RecipeForBuildingLevel("clay_quarry_run", 99)
	if last.RequiredLevel != 12 {
		t.Fatalf("expected level 12 clamp, got %#v", last)
	}
}

func TestGlassWorkshopRecipeForBuildingLevel(t *testing.T) {
	levelOne, ok := RecipeForBuildingLevel("glass_batch", 1)
	if !ok {
		t.Fatal("glass workshop recipe not found")
	}
	if levelOne.Duration != 13*time.Minute+20*time.Second || levelOne.Workers != 6 {
		t.Fatalf("unexpected level 1 glass workshop recipe: %#v", levelOne)
	}
	assertOutput(t, levelOne.Output, economy.ResourceGlass, 1)
	assertInput(t, levelOne.Input, economy.ResourceSand, 28)
	assertInput(t, levelOne.Input, economy.ResourceCoal, 1)
	if len(levelOne.RareOutput) != 0 || levelOne.FuelPerRun != 0 {
		t.Fatalf("level 1 should use coal without rare output: %#v", levelOne)
	}

	levelFive, _ := RecipeForBuildingLevel("glass_batch", 5)
	if levelFive.Duration != 17*time.Minute+40*time.Second || levelFive.Workers != 13 {
		t.Fatalf("unexpected level 5 glass workshop recipe: %#v", levelFive)
	}
	assertOutput(t, levelFive.Output, economy.ResourceGlass, 3)
	if len(levelFive.RareOutput) != 2 || levelFive.RareOutput[0].Resource != economy.ResourceStarGlass || levelFive.RareOutput[0].Chance != 0.008 || levelFive.RareOutput[1].Resource != economy.ResourceLightCrystal || levelFive.RareOutput[1].Chance != 0.0001 {
		t.Fatalf("unexpected level 5 rare output: %#v", levelFive.RareOutput)
	}

	levelNine, _ := RecipeForBuildingLevel("glass_batch", 99)
	if levelNine.RequiredLevel != 9 || levelNine.Duration != 45*time.Minute || levelNine.Workers != 24 || levelNine.FuelPerRun != 26 {
		t.Fatalf("unexpected clamped level 9 glass workshop recipe: %#v", levelNine)
	}
	assertInput(t, levelNine.Input, economy.ResourceSand, 87)
	assertOutput(t, levelNine.Output, economy.ResourceGlass, 7)
}

func assertOutput(t *testing.T, output []economy.ResourceAmount, resource economy.ResourceType, amount int) {
	t.Helper()
	for _, item := range output {
		if item.Resource == resource {
			if item.Amount != amount {
				t.Fatalf("expected %s output %d, got %d", resource, amount, item.Amount)
			}
			return
		}
	}
	t.Fatalf("missing output resource %s in %#v", resource, output)
}

func assertInput(t *testing.T, input []economy.ResourceAmount, resource economy.ResourceType, amount int) {
	t.Helper()
	for _, item := range input {
		if item.Resource == resource {
			if item.Amount != amount {
				t.Fatalf("expected %s input %d, got %d", resource, amount, item.Amount)
			}
			return
		}
	}
	t.Fatalf("missing input resource %s in %#v", resource, input)
}
