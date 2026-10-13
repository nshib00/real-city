package catalog

import (
	"time"

	"real-city/backend/internal/domain/monster"
)

var monsterSpecs = []monster.Spec{
	{
		Type:           monster.TypeRoamingMelee,
		Name:           "Бродячий налетчик",
		MaxHealth:      180,
		Damage:         18,
		SpeedTiles:     1,
		AggroRadius:    5,
		AttackRange:    1,
		AttackCooldown: 8 * time.Second,
		LootCoins:      65,
		SpawnWeight:    24,
	},
	{
		Type:           monster.TypeResourceGuardian,
		Name:           "Страж залежи",
		MaxHealth:      280,
		Damage:         26,
		SpeedTiles:     1,
		AggroRadius:    4,
		AttackRange:    1,
		AttackCooldown: 10 * time.Second,
		LootCoins:      120,
		SpawnWeight:    18,
	},
	{
		Type:           monster.TypeRuinsGuardian,
		Name:           "Сторож руин",
		MaxHealth:      420,
		Damage:         38,
		SpeedTiles:     1,
		AggroRadius:    6,
		AttackRange:    1,
		AttackCooldown: 12 * time.Second,
		LootCoins:      220,
		SpawnWeight:    10,
	},
	{
		Type:           monster.TypeForestStalker,
		Name:           "Лесной следопыт",
		MaxHealth:      150,
		Damage:         14,
		SpeedTiles:     2,
		AggroRadius:    6,
		AttackRange:    1,
		AttackCooldown: 6 * time.Second,
		LootCoins:      55,
		SpawnWeight:    28,
	},
	{
		Type:           monster.TypeSporeBeast,
		Name:           "Споровый зверь",
		MaxHealth:      320,
		Damage:         22,
		SpeedTiles:     1,
		AggroRadius:    4,
		AttackRange:    1,
		AttackCooldown: 10 * time.Second,
		LootCoins:      130,
		SpawnWeight:    20,
	},
	{
		Type:           monster.TypeIronbackBrute,
		Name:           "Железоспин",
		MaxHealth:      620,
		Damage:         44,
		SpeedTiles:     1,
		AggroRadius:    5,
		AttackRange:    1,
		AttackCooldown: 14 * time.Second,
		LootCoins:      320,
		SpawnWeight:    8,
	},
	{
		Type:           monster.TypeEmberWisp,
		Name:           "Тлеющий огонек",
		MaxHealth:      240,
		Damage:         16,
		SpeedTiles:     1,
		AggroRadius:    7,
		AttackRange:    3,
		AttackCooldown: 9 * time.Second,
		LootCoins:      180,
		SpawnWeight:    12,
	},
	{
		Type:           monster.TypeAncientColossus,
		Name:           "Древний колосс",
		MaxHealth:      2400,
		Damage:         120,
		SpeedTiles:     1,
		AggroRadius:    8,
		AttackRange:    1,
		AttackCooldown: 18 * time.Second,
		LootCoins:      2200,
		SpawnWeight:    1,
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
