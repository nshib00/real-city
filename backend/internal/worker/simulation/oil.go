package simulation

import "real-city/backend/internal/domain/economy"

func IsOilNode(node economy.ResourceNode) bool {
	return node.Resource == economy.ResourceOil || node.Type == "oil_well"
}
