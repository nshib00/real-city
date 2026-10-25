package catalog

import (
	"testing"

	"real-city/backend/internal/domain/building"
)

func TestDefenseBuildingCosts(t *testing.T) {
	tests := []struct {
		buildingType building.Type
		coinCosts    []int
	}{
		{building.TypeTower, []int{15000}},
		{building.TypeWoodenWall, []int{1000, 1800, 3200}},
		{building.TypeConcreteWall, []int{30000, 86000, 170000}},
		{building.TypeModernWall, []int{250000, 420000, 760000}},
	}

	for _, test := range tests {
		t.Run(string(test.buildingType), func(t *testing.T) {
			definition := Buildings[test.buildingType]
			if got := resourceCost(definition.Cost, "coins"); got != test.coinCosts[0] {
				t.Fatalf("base coins = %d, want %d", got, test.coinCosts[0])
			}
			if len(test.coinCosts) == 1 {
				return
			}
			if len(definition.UpgradeLevels) != len(test.coinCosts) {
				t.Fatalf("upgrade levels = %d, want %d", len(definition.UpgradeLevels), len(test.coinCosts))
			}
			for index, level := range definition.UpgradeLevels {
				if got := resourceCost(level.Cost, "coins"); got != test.coinCosts[index] {
					t.Errorf("level %d coins = %d, want %d", level.Level, got, test.coinCosts[index])
				}
				seen := make(map[string]bool)
				for _, cost := range level.Cost {
					if seen[cost.Resource] {
						t.Errorf("level %d repeats %s", level.Level, cost.Resource)
					}
					seen[cost.Resource] = true
				}
			}
		})
	}
}

func resourceCost(costs []building.Cost, resource string) int {
	for _, cost := range costs {
		if cost.Resource == resource {
			return cost.Amount
		}
	}
	return 0
}
