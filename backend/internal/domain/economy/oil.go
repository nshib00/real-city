package economy

import "real-city/backend/internal/domain/world"

func OilWellNode(id NodeID, mapID string, x int, y int, amount int) ResourceNode {
	return ResourceNode{
		ID:        id,
		MapID:     mapID,
		Type:      "oil_well",
		Resource:  ResourceOil,
		Amount:    amount,
		MaxAmount: amount,
		State:     NodeNeutral,
		Tile:      world.Coord{X: x, Y: y},
	}
}
