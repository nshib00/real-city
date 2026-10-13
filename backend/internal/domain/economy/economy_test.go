package economy

import (
	"testing"
	"time"
)

func TestInventorySpendAndAdd(t *testing.T) {
	now := time.Date(2026, 8, 25, 12, 0, 0, 0, time.UTC)
	inventory := NewInventory("p1", now, 2000)
	inventory.Items[ResourceWood] = 420

	if !inventory.Spend([]ResourceAmount{{Resource: ResourceWood, Amount: 40}}, now) {
		t.Fatal("expected wood spend to succeed")
	}
	if inventory.Items[ResourceWood] != 380 {
		t.Fatalf("unexpected wood amount: %d", inventory.Items[ResourceWood])
	}
	if inventory.Spend([]ResourceAmount{{Resource: ResourceWood, Amount: 10000}}, now) {
		t.Fatal("expected overspend to fail")
	}
}

func TestInventoryOnlyCoinsHaveCapacity(t *testing.T) {
	now := time.Date(2026, 8, 25, 12, 0, 0, 0, time.UTC)
	inventory := Inventory{
		PlayerID:     "p1",
		CoinCapacity: 2000,
		Items: map[ResourceType]int{
			ResourceCoins: 1900,
			ResourceWood:  12000,
		},
	}

	overflow := inventory.Add([]ResourceAmount{
		{Resource: ResourceCoins, Amount: 250},
		{Resource: ResourceWood, Amount: 50000},
	}, now)

	if inventory.Items[ResourceCoins] != 2000 {
		t.Fatalf("coins should be capped at 2000, got %d", inventory.Items[ResourceCoins])
	}
	if len(overflow) != 1 || overflow[0].Amount != 150 {
		t.Fatalf("expected 150 coin overflow, got %#v", overflow)
	}
	if inventory.Items[ResourceWood] != 62000 {
		t.Fatalf("wood should not be capped, got %d", inventory.Items[ResourceWood])
	}
}

func TestWindleafCropHasSuperChanceAndRewards(t *testing.T) {
	crop := WindleafCropForLevel(11)
	if crop.SuperChanceBps != 75 {
		t.Fatalf("super chance should match level 11 balance, got %d bps", crop.SuperChanceBps)
	}
	if crop.CoinReward != 86000 || len(crop.BaseReward) != 1 || crop.BaseReward[0].Amount != 11 {
		t.Fatalf("unexpected level 11 windleaf reward: %#v", crop)
	}
	if len(crop.Growth) != 4 || !crop.Growth[3].Ready {
		t.Fatalf("expected four growth stages with ready final stage: %#v", crop.Growth)
	}
	if crop.Growth[0].Duration != 206250*time.Millisecond {
		t.Fatalf("expected equal stage duration for level 11, got %s", crop.Growth[0].Duration)
	}
	levelOne := WindleafCrop()
	if levelOne.SuperChanceBps != 0 || levelOne.CoinReward != 190 {
		t.Fatalf("unexpected level 1 crop balance: %#v", levelOne)
	}
}

func TestSeedGardenCropMatchesSpecRewards(t *testing.T) {
	crop, ok := FieldCropForBuildingType("seed_garden", 10, false)
	if !ok {
		t.Fatal("expected seed garden crop")
	}
	if crop.CoinReward != 18000 || len(crop.BaseReward) != 1 || crop.BaseReward[0] != (ResourceAmount{Resource: ResourceSeeds, Amount: 70}) {
		t.Fatalf("unexpected regular seed garden reward: %#v", crop)
	}
	if len(crop.Growth) != 3 || crop.Growth[0].Duration != 450*time.Second || !crop.Growth[2].Ready {
		t.Fatalf("unexpected seed garden growth: %#v", crop.Growth)
	}
	superCrop, ok := FieldCropForBuildingType("seed_garden", 10, true)
	if !ok {
		t.Fatal("expected seed garden super crop")
	}
	if superCrop.SuperCoinReward != 198000 || len(superCrop.SuperReward) != 2 || superCrop.SuperReward[1] != (ResourceAmount{Resource: ResourceSuperSeeds, Amount: 2}) {
		t.Fatalf("unexpected seed garden super reward: %#v", superCrop)
	}
	if len(superCrop.Growth) != 6 || superCrop.Growth[0].Duration != 1890*time.Second || !superCrop.Growth[5].Ready {
		t.Fatalf("unexpected seed garden super growth: %#v", superCrop.Growth)
	}
}

func TestFlaxFieldCropMatchesSpecRewards(t *testing.T) {
	crop, ok := FieldCropForBuildingType("flax_field", 10, false)
	if !ok {
		t.Fatal("expected flax field crop")
	}
	if crop.CoinReward != 12800 || len(crop.BaseReward) != 1 || crop.BaseReward[0] != (ResourceAmount{Resource: ResourceFlax, Amount: 132}) {
		t.Fatalf("unexpected regular flax reward: %#v", crop)
	}
	if len(crop.Growth) != 3 || crop.Growth[0].Duration != 600*time.Second || !crop.Growth[2].Ready {
		t.Fatalf("unexpected flax growth: %#v", crop.Growth)
	}
	superCrop, ok := FieldCropForBuildingType("flax_field", 10, true)
	if !ok {
		t.Fatal("expected flax super crop")
	}
	if superCrop.SuperCoinReward != 51200 || len(superCrop.SuperReward) != 2 || superCrop.SuperReward[1] != (ResourceAmount{Resource: ResourceSuperFiber, Amount: 2}) {
		t.Fatalf("unexpected flax super reward: %#v", superCrop)
	}
	if len(superCrop.Growth) != 6 || superCrop.Growth[0].Duration != 2160*time.Second || !superCrop.Growth[5].Ready {
		t.Fatalf("unexpected flax super growth: %#v", superCrop.Growth)
	}
}

func TestAllFieldBuildingTypesHaveCropSpecs(t *testing.T) {
	for _, buildingType := range []string{
		"field_bed",
		"seed_garden",
		"herb_bed",
		"mushroom_grove",
		"flax_field",
		"reed_bed",
		"dye_garden",
		"oilseed_field",
		"sugar_bed",
		"crystal_greenhouse",
	} {
		crop, ok := FieldCropForBuildingType(buildingType, 1, false)
		if !ok {
			t.Fatalf("missing crop spec for %s", buildingType)
		}
		if len(crop.Growth) == 0 || len(crop.BaseReward) == 0 || crop.CoinReward <= 0 {
			t.Fatalf("incomplete crop spec for %s: %#v", buildingType, crop)
		}
	}
}
