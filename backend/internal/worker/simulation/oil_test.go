package simulation

import (
	"testing"

	"real-city/backend/internal/domain/economy"
)

func TestIsOilNode(t *testing.T) {
	if !IsOilNode(economy.ResourceNode{Resource: economy.ResourceOil}) {
		t.Fatal("expected oil resource node")
	}
	if IsOilNode(economy.ResourceNode{Resource: economy.ResourceWood}) {
		t.Fatal("wood node should not be oil")
	}
}
