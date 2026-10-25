package catalog

import (
	"testing"

	"real-city/backend/internal/domain/building"
)

func TestDemolitionRefundIncludesBuildAndUpgradeCosts(t *testing.T) {
	for _, test := range []struct {
		kind  building.Type
		level int
		want  int
	}{
		{building.TypeDugout, 1, 10},
		{building.TypeDugout, 2, 90},
		{building.TypeWoodHouse, 1, 4140},
		{building.TypeOilWell, 1, 550},
	} {
		if got := DemolitionRefundCoins(test.kind, test.level); got != test.want {
			t.Fatalf("refund for %s level %d: got %d, want %d", test.kind, test.level, got, test.want)
		}
	}
}
