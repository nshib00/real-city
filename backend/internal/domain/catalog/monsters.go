package catalog

import (
	"time"

	"real-city/backend/internal/domain/monster"
)

var monsterSpecs = []monster.Spec{
	{
		Type:           monster.TypeRoamingMelee,
		Name:           "Бродячий налетчик",
		MaxHealth:      90,
		Damage:         8,
		SpeedTiles:     1,
		AggroRadius:    5,
		AttackRange:    1,
		AttackCooldown: 8 * time.Second,
		LootCoins:      18,
	},
	{
		Type:           monster.TypeResourceGuardian,
		Name:           "Страж залежи",
		MaxHealth:      140,
		Damage:         12,
		SpeedTiles:     1,
		AggroRadius:    4,
		AttackRange:    1,
		AttackCooldown: 10 * time.Second,
		LootCoins:      34,
	},
	{
		Type:           monster.TypeRuinsGuardian,
		Name:           "Сторож руин",
		MaxHealth:      210,
		Damage:         18,
		SpeedTiles:     1,
		AggroRadius:    6,
		AttackRange:    1,
		AttackCooldown: 12 * time.Second,
		LootCoins:      58,
	},
}

func MonsterSpecs() []monster.Spec {
	items := make([]monster.Spec, len(monsterSpecs))
	copy(items, monsterSpecs)
	return items
}

func MonsterSpec(kind monster.Type) (monster.Spec, bool) {
	for _, spec := range monsterSpecs {
		if spec.Type == kind {
			return spec, true
		}
	}
	return monster.Spec{}, false
}
