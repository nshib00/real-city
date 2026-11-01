package service

import (
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"testing"
)

func TestMineRareAlternativesHaveDocumentedProbabilities(t *testing.T) {
	for _, tc := range []struct {
		roll float64
		coal int
	}{{0, 1}, {.449, 1}, {.45, 2}, {.499, 2}, {.5, 0}} {
		s := ProductionService{randFloat: func() float64 { return tc.roll }}
		r, _ := catalog.RecipeForBuildingLevel("mine_run", 2)
		coal := 0
		for _, out := range s.rollRareOutput(r) {
			if out.Resource == economy.ResourceCoal {
				coal += out.Amount
			}
		}
		if coal != tc.coal {
			t.Fatal(tc, coal)
		}
	}
	s := ProductionService{randFloat: func() float64 { return .205 }}
	r, _ := catalog.RecipeForBuildingLevel("mine_run", 11)
	copper := 0
	for _, out := range s.rollRareOutput(r) {
		if out.Resource == economy.ResourceCopper {
			copper += out.Amount
		}
	}
	if copper != 2 {
		t.Fatal("two-copper interval was not a separate alternative", copper)
	}
}
