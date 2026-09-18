package combat

import (
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
)

type AttackResult struct {
	Monster      monster.Monster
	Damage       int
	Killed       bool
	Reward       []economy.ResourceAmount
	NextAttackAt time.Time
}

func PlayerAttackMonster(target monster.Monster, damage int, now time.Time) AttackResult {
	if damage <= 0 {
		damage = 25
	}
	killed := target.ApplyDamage(damage, now)
	reward := []economy.ResourceAmount(nil)
	if killed && target.LootCoins > 0 {
		reward = []economy.ResourceAmount{{Resource: economy.ResourceCoins, Amount: target.LootCoins}}
	}
	return AttackResult{Monster: target, Damage: damage, Killed: killed, Reward: reward, NextAttackAt: now.Add(5 * time.Second)}
}
