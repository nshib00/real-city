package economy

import "testing"

func TestWithFuelCostAppendsFuelPerRun(t *testing.T) {
	recipe := ProductionRecipe{FuelPerRun: 3}
	cost := WithFuelCost([]ResourceAmount{{Resource: ResourceOil, Amount: 8}}, recipe)
	if len(cost) != 2 {
		t.Fatalf("cost len = %d", len(cost))
	}
	if cost[1].Resource != ResourceFuel || cost[1].Amount != 3 {
		t.Fatalf("unexpected fuel cost: %#v", cost[1])
	}
}
