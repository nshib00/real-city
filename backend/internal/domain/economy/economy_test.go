package economy

import (
	"testing"
	"time"
)

func TestInventorySpendAndAdd(t *testing.T) {
	now := time.Date(2026, 8, 25, 12, 0, 0, 0, time.UTC)
	inventory := NewInventory("p1", now, 2000)

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
