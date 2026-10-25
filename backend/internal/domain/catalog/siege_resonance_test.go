package catalog

import (
	"testing"

	"real-city/backend/internal/domain/building"
)

func TestSiegeAndResonanceBuildingProgression(t *testing.T) {
	yard, ok := GetBuilding(building.TypeSiegeYard)
	if !ok || len(yard.UpgradeLevels) != 2 {
		t.Fatalf("siege yard levels = %d, exists = %t", len(yard.UpgradeLevels), ok)
	}
	if yard.UpgradeLevels[0].Cost[0].Amount != 1700000 || yard.UpgradeLevels[1].Cost[0].Amount != 4300000 {
		t.Fatalf("unexpected siege yard coin costs: %+v", yard.UpgradeLevels)
	}
	laboratory, ok := GetBuilding(building.TypeResonanceLaboratory)
	if !ok || len(laboratory.UpgradeLevels) != 1 || laboratory.Cost[0].Amount != 9000000 {
		t.Fatalf("unexpected resonance laboratory: %+v, exists = %t", laboratory, ok)
	}
	for _, test := range []struct {
		id       string
		building string
		level    int
	}{
		{"siege_mine_batch", "siege_yard", 1},
		{"breach_bomb_batch", "siege_yard", 2},
		{"resonance_charge_batch", "resonance_laboratory", 1},
	} {
		recipe, found := RecipeByID(test.id)
		if !found || recipe.BuildingType != test.building || recipe.RequiredLevel != test.level {
			t.Errorf("recipe %s = %+v, found = %t", test.id, recipe, found)
		}
	}
}
