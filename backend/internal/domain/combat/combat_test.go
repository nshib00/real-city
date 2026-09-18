package combat

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/monster"
)

func TestPlayerAttackMonsterReturnsLootOnKill(t *testing.T) {
	target := monster.Monster{State: monster.StateAggro, Health: 20, LootCoins: 7}
	result := PlayerAttackMonster(target, 25, time.Now())
	if !result.Killed {
		t.Fatal("expected kill")
	}
	if len(result.Reward) != 1 || result.Reward[0].Amount != 7 {
		t.Fatalf("expected coin reward, got %+v", result.Reward)
	}
}
