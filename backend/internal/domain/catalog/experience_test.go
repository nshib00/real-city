package catalog

import (
	"testing"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
)

func TestBuildingXPPolicyCoversEveryTypeLevelAndRecipe(t *testing.T) {
	destructionRewards := make(map[int]bool)
	completionRewards := make(map[int]bool)
	specs := AllBuildings()
	for _, ruin := range RuinSpecs {
		specs = append(specs, ruin)
	}
	for _, spec := range specs {
		levels := spec.UpgradeLevels
		if len(levels) == 0 {
			levels = []BuildingUpgradeLevel{{Level: spec.Level}}
		}
		previous := 0
		for _, level := range levels {
			xp := ExperienceForBuilding(spec.Type, level.Level)
			if xp.Completion <= 0 || xp.Destruction <= previous || xp.Destruction > 500000 || xp.Work < 0 {
				t.Fatalf("invalid XP policy for %s/%d: %+v", spec.Type, level.Level, xp)
			}
			previous = xp.Destruction
			if xp.Destruction%5 == 0 || destructionRewards[xp.Destruction] {
				t.Fatalf("round or duplicate destruction XP for %s/%d: %d", spec.Type, level.Level, xp.Destruction)
			}
			destructionRewards[xp.Destruction] = true
			if xp.Completion >= 100 {
				if xp.Completion%5 == 0 || completionRewards[xp.Completion] {
					t.Fatalf("round or duplicate completion XP for %s/%d: %d", spec.Type, level.Level, xp.Completion)
				}
				completionRewards[xp.Completion] = true
			}
			working := economy.IsFieldCropBuildingType(string(spec.Type)) || spec.Type == building.TypeOilWell
			for _, recipe := range ProductionCatalog() {
				working = working || recipe.BuildingType == string(spec.Type)
			}
			if working && xp.Work <= 0 {
				t.Fatalf("missing work XP for %s/%d", spec.Type, level.Level)
			}
		}
	}
}

func TestBuildingXPUsesGlobalLevelsAndLateGameProgression(t *testing.T) {
	for _, tc := range []struct {
		kind  building.Type
		level int
		want  int
	}{
		{building.TypeDugout, 1, 11},
		{building.TypeWoodenWall, 1, 19},
		{building.TypeModernWall, 13, 493817},
		{building.TypeGlassWorkshop, 12, 497681},
		{building.TypeLumberYard, 13, 448631},
		{building.TypeCoinStorage, 12, 487263},
	} {
		if got := ExperienceForBuilding(tc.kind, tc.level).Destruction; got != tc.want {
			t.Fatalf("%s/%d: got %d, want %d", tc.kind, tc.level, got, tc.want)
		}
	}
	if ExperienceForBuilding(building.TypeModernWall, 1) != (BuildingXP{}) {
		t.Fatal("wall rewards must not be indexed by position in the level array")
	}
	for _, tc := range []struct {
		from, to building.Type
		level    int
	}{
		{building.TypeDugout, building.TypeWoodHouse, 5},
		{building.TypeWoodHouse, building.TypeStoneHouse, 6},
	} {
		if ExperienceForBuilding(tc.to, 1).Destruction <= ExperienceForBuilding(tc.from, tc.level).Destruction {
			t.Fatal("housing transition reduces destruction XP")
		}
	}
}
