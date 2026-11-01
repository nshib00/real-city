package catalog

import (
	"reflect"
	"testing"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
)

func TestCannonLevelsMatchSpecification(t *testing.T) {
	want := []struct {
		minutes, builders, health, radius, damage int
		cost                                      []building.Cost
		ammo                                      economy.ResourceType
	}{
		{8, 2, 260, 2, 55, []building.Cost{{Resource: "coins", Amount: 1750}, {Resource: "planks", Amount: 12}, {Resource: "rope", Amount: 3}}, economy.ResourceStone},
		{12, 2, 310, 2, 68, []building.Cost{{Resource: "coins", Amount: 2600}, {Resource: "planks", Amount: 20}, {Resource: "rope", Amount: 5}}, economy.ResourceStone},
		{18, 3, 370, 3, 82, []building.Cost{{Resource: "coins", Amount: 3900}, {Resource: "planks", Amount: 18}, {Resource: "stone_block", Amount: 12}, {Resource: "iron_ingot", Amount: 2}}, economy.ResourceStone},
		{25, 3, 450, 3, 100, []building.Cost{{Resource: "coins", Amount: 5800}, {Resource: "stone_block", Amount: 20}, {Resource: "iron_ingot", Amount: 6}}, economy.ResourceStone},
		{35, 4, 540, 3, 122, []building.Cost{{Resource: "coins", Amount: 8500}, {Resource: "stone_block", Amount: 30}, {Resource: "iron_ingot", Amount: 10}}, economy.ResourceStone},
		{50, 4, 650, 4, 148, []building.Cost{{Resource: "coins", Amount: 12500}, {Resource: "stone_block", Amount: 40}, {Resource: "iron_ingot", Amount: 16}}, economy.ResourceStone},
		{70, 5, 780, 4, 180, []building.Cost{{Resource: "coins", Amount: 18500}, {Resource: "stone_block", Amount: 55}, {Resource: "mechanism", Amount: 6}}, economy.ResourceExplosives},
		{95, 5, 930, 4, 215, []building.Cost{{Resource: "coins", Amount: 28000}, {Resource: "stone_block", Amount: 70}, {Resource: "mechanism", Amount: 10}, {Resource: "armor_plates", Amount: 4}}, economy.ResourceExplosives},
		{130, 6, 1100, 5, 255, []building.Cost{{Resource: "coins", Amount: 42000}, {Resource: "stone_block", Amount: 85}, {Resource: "mechanism", Amount: 14}, {Resource: "armor_plates", Amount: 8}}, economy.ResourceExplosives},
		{175, 6, 1300, 5, 300, []building.Cost{{Resource: "coins", Amount: 65000}, {Resource: "mechanism", Amount: 18}, {Resource: "armor_plates", Amount: 14}, {Resource: "electronics", Amount: 4}}, economy.ResourceExplosives},
		{230, 7, 1530, 5, 350, []building.Cost{{Resource: "coins", Amount: 98000}, {Resource: "mechanism", Amount: 24}, {Resource: "armor_plates", Amount: 22}, {Resource: "electronics", Amount: 8}}, economy.ResourceExplosives},
		{300, 8, 1800, 6, 410, []building.Cost{{Resource: "coins", Amount: 150000}, {Resource: "mechanism", Amount: 30}, {Resource: "armor_plates", Amount: 32}, {Resource: "electronics", Amount: 14}}, economy.ResourceExplosives},
	}
	definition := Buildings[building.TypeDefenseCannon]
	if !definition.CountsTowardLimit || definition.Footprint != (building.Footprint{Width: 1, Height: 1}) || len(definition.UpgradeLevels) != len(want) {
		t.Fatalf("invalid cannon definition: %+v", definition)
	}
	for i, expected := range want {
		level := definition.UpgradeLevels[i]
		stats, ok := CannonLevel(i + 1)
		if !ok || level.Level != i+1 || level.BuildDuration != time.Duration(expected.minutes)*time.Minute ||
			level.Population != expected.builders || level.Health != expected.health || !reflect.DeepEqual(level.Cost, expected.cost) ||
			stats.Range != expected.radius || stats.Damage != expected.damage || stats.Ammo != expected.ammo {
			t.Errorf("level %d differs from cannon specification: level=%+v stats=%+v", i+1, level, stats)
		}
	}
	if refund := DemolitionRefundCoins(building.TypeDefenseCannon, 12); refund != 87310 {
		t.Fatalf("level 12 demolition refund = %d, want 87310", refund)
	}
}
