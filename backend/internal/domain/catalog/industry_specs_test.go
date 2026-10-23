package catalog

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
)

func TestIndustrySpecificationLevelsArePlayable(t *testing.T) {
	cases := []struct {
		kind   building.Type
		recipe string
		output economy.ResourceType
	}{
		{building.TypeCementWorkshop, "cement_batch", economy.ResourceCement},
		{building.TypeConcretePlant, "concrete_batch", economy.ResourceConcrete},
		{building.TypePaperWorkshop, "paper_batch", economy.ResourcePaper},
		{building.TypeWeavingYard, "fabric_batch", economy.ResourceFabric},
		{building.TypeMilitaryPlant, "explosives_batch", economy.ResourceExplosives},
		{building.TypeTileFactory, "tile_batch", economy.ResourceTile},
		{building.TypeBrickYard, "brick_yard_batch", economy.ResourceBrick},
		{building.TypeFoundry, "iron_ingot_batch", economy.ResourceIronIngot},
		{building.TypeOilPress, "plant_oil_batch", economy.ResourcePlantOil},
		{building.TypeOilRefinery, "fuel_from_oil", economy.ResourceFuel},
		{building.TypeResinKiln, "resin_batch", economy.ResourceResin},
		{building.TypeSteelworks, "steel_batch", economy.ResourceSteel},
		{building.TypeSulfurSpring, "sulfur_batch", economy.ResourceSulfur},
		{building.TypeElectronics, "electronics_batch", economy.ResourceElectronics},
		{building.TypeMechanicalShop, "copper_parts_batch", economy.ResourceCopperParts},
		{building.TypePaintWorkshop, "paint_batch", economy.ResourcePaints},
		{building.TypeCopperMine, "copper_mine_batch", economy.ResourceCopper},
	}
	for _, test := range cases {
		spec, ok := GetBuilding(test.kind)
		if !ok || len(spec.UpgradeLevels) != 10 || spec.Health != spec.UpgradeLevels[0].Health {
			t.Fatalf("incomplete catalog for %s: %#v", test.kind, spec)
		}
		for level := 1; level <= 10; level++ {
			upgrade := spec.UpgradeLevels[level-1]
			recipe, found := RecipeForBuildingLevel(test.recipe, level)
			xp := ExperienceForBuilding(test.kind, level)
			if !found || upgrade.Level != level || upgrade.Health <= 0 || upgrade.BuildDuration <= 0 || len(upgrade.Cost) == 0 ||
				recipe.RequiredLevel != level || recipe.BuildingType != string(test.kind) || recipe.Workers != upgrade.Population ||
				recipe.Duration <= 0 || len(recipe.Output) != 1 || recipe.Output[0].Resource != test.output ||
				xp.Completion <= 0 || xp.Work <= 0 || xp.Destruction <= 0 {
				t.Fatalf("incomplete level %d for %s: upgrade=%#v recipe=%#v xp=%#v", level, test.kind, upgrade, recipe, xp)
			}
		}
	}
}

func TestResinKilnRareOutputMatchesSpecification(t *testing.T) {
	for _, tc := range []struct {
		level  int
		chance float64
	}{{1, 0}, {4, 0.01}, {10, 0.04}} {
		recipe, ok := RecipeForBuildingLevel("resin_batch", tc.level)
		if !ok {
			t.Fatalf("missing resin recipe at level %d", tc.level)
		}
		if tc.chance == 0 {
			if len(recipe.RareOutput) != 0 {
				t.Fatalf("unexpected rare output at level %d: %#v", tc.level, recipe.RareOutput)
			}
			continue
		}
		if len(recipe.RareOutput) != 1 || recipe.RareOutput[0].Resource != economy.ResourceOleoresin || recipe.RareOutput[0].Amount != 1 || recipe.RareOutput[0].Chance != tc.chance {
			t.Fatalf("incorrect rare output at level %d: %#v", tc.level, recipe.RareOutput)
		}
	}
}

func TestAdditionalIndustryRecipesFollowSpecifications(t *testing.T) {
	cases := []struct {
		id      string
		minimum int
		minutes int
		input   []economy.ResourceAmount
		output  economy.ResourceAmount
		fuel    int
	}{
		{"reinforced_concrete_batch", 6, 60, []economy.ResourceAmount{{economy.ResourceConcrete, 12}, {economy.ResourceSteel, 3}}, economy.ResourceAmount{economy.ResourceReinforcedConc, 8}, 18},
		{"armor_plates_batch", 5, 65, []economy.ResourceAmount{{economy.ResourceSteel, 8}, {economy.ResourceConcrete, 10}}, economy.ResourceAmount{economy.ResourceArmorPlates, 4}, 20},
		{"rune_tile_batch", 8, 90, []economy.ResourceAmount{{economy.ResourceTile, 12}, {economy.ResourceQuietPowder, 1}, {economy.ResourceMemoryShard, 1}, {economy.ResourceCoal, 25}}, economy.ResourceAmount{economy.ResourceRuneTile, 1}, 0},
	}
	for _, test := range cases {
		recipe, ok := RecipeForBuildingLevel(test.id, test.minimum)
		if !ok || recipe.RequiredLevel != test.minimum || recipe.Duration != time.Duration(test.minutes)*time.Minute ||
			recipe.FuelPerRun != test.fuel || len(recipe.Input) != len(test.input) || len(recipe.Output) != 1 || recipe.Output[0] != test.output {
			t.Fatalf("incorrect recipe %s: %#v", test.id, recipe)
		}
		for index, input := range test.input {
			if recipe.Input[index] != input {
				t.Fatalf("incorrect input for %s: %#v", test.id, recipe.Input)
			}
		}
	}
}

func TestWoodenWallUpgradeLevelsRemainExact(t *testing.T) {
	spec, ok := GetBuilding(building.TypeWoodenWall)
	if !ok || len(spec.UpgradeLevels) != 3 {
		t.Fatalf("wooden wall levels: %#v", spec)
	}
	for index, health := range []int{120, 200, 320} {
		if spec.UpgradeLevels[index].Health != health {
			t.Fatalf("wooden wall level %d health: %d", index+1, spec.UpgradeLevels[index].Health)
		}
	}
}
