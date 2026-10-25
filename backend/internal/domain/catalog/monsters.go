package catalog

import (
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
)

var monsterSpecs = []monster.Spec{
	{
		Type:           monster.TypeRoamingMelee,
		Name:           "Бродячий налетчик",
		MaxHealth:      360,
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
		MaxHealth:      560,
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
		MaxHealth:      840,
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
		MaxHealth:      300,
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
		MaxHealth:      640,
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
		MaxHealth:      1240,
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
		MaxHealth:      480,
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
		MaxHealth:      300000,
		Damage:         2400,
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

// MonsterPrefersBuilding reports whether a building belongs to the monster's
// first-choice target group. Targets outside that group remain valid fallback targets.
func MonsterPrefersBuilding(kind monster.Type, target building.Type) bool {
	spec, ok := GetBuilding(target)
	if !ok {
		return false
	}
	switch kind {
	case monster.TypeRoamingMelee:
		return spec.Category == "housing"
	case monster.TypeResourceGuardian:
		switch target {
		case building.TypeSandQuarry, building.TypeClayQuarry, building.TypeMine,
			building.TypeIronMine, building.TypeCopperMine, building.TypeOilWell,
			building.TypeSulfurSpring, building.TypeStoneCutters:
			return true
		}
	case monster.TypeRuinsGuardian:
		return spec.Category == "storage" || spec.Category == "trade"
	case monster.TypeForestStalker:
		return target == building.TypeLumberYard || target == building.TypeResinKiln
	case monster.TypeSporeBeast:
		return spec.Category == "fields"
	case monster.TypeIronbackBrute:
		return spec.Category == "defense" && !building.IsTrapType(target)
	case monster.TypeEmberWisp:
		return spec.Category == "industry" || spec.Category == "storage"
	case monster.TypeAncientColossus:
		return target == building.TypeTownHall
	}
	return false
}
