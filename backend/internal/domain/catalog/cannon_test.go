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
		{8, 2, 260, 2, 55, []building.Cost{{"coins", 1750}, {"planks", 12}, {"rope", 3}}, economy.ResourceStone},
		{12, 2, 310, 2, 68, []building.Cost{{"coins", 2600}, {"planks", 20}, {"rope", 5}}, economy.ResourceStone},
		{18, 3, 370, 3, 82, []building.Cost{{"coins", 3900}, {"planks", 18}, {"stone_block", 12}, {"iron_ingot", 2}}, economy.ResourceStone},
		{25, 3, 450, 3, 100, []building.Cost{{"coins", 5800}, {"stone_block", 20}, {"iron_ingot", 6}}, economy.ResourceStone},
		{35, 4, 540, 3, 122, []building.Cost{{"coins", 8500}, {"stone_block", 30}, {"iron_ingot", 10}}, economy.ResourceStone},
		{50, 4, 650, 4, 148, []building.Cost{{"coins", 12500}, {"stone_block", 40}, {"iron_ingot", 16}}, economy.ResourceStone},
		{70, 5, 780, 4, 180, []building.Cost{{"coins", 18500}, {"stone_block", 55}, {"mechanism", 6}}, economy.ResourceExplosives},
		{95, 5, 930, 4, 215, []building.Cost{{"coins", 28000}, {"stone_block", 70}, {"mechanism", 10}, {"armor_plates", 4}}, economy.ResourceExplosives},
		{130, 6, 1100, 5, 255, []building.Cost{{"coins", 42000}, {"stone_block", 85}, {"mechanism", 14}, {"armor_plates", 8}}, economy.ResourceExplosives},
		{175, 6, 1300, 5, 300, []building.Cost{{"coins", 65000}, {"mechanism", 18}, {"armor_plates", 14}, {"electronics", 4}}, economy.ResourceExplosives},
		{230, 7, 1530, 5, 350, []building.Cost{{"coins", 98000}, {"mechanism", 24}, {"armor_plates", 22}, {"electronics", 8}}, economy.ResourceExplosives},
		{300, 8, 1800, 6, 410, []building.Cost{{"coins", 150000}, {"mechanism", 30}, {"armor_plates", 32}, {"electronics", 14}}, economy.ResourceExplosives},
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
