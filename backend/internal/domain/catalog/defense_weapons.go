package catalog

import (
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
)

type DefenseWeaponStats struct {
	Range      int
	Damage     int
	Cooldown   time.Duration
	DamageType string
	Ammo       economy.ResourceType
}

var boltThrowerStats = [...]DefenseWeaponStats{
	{2, 18, 5 * time.Second, "piercing", ""},
	{2, 23, 5 * time.Second, "piercing", ""},
	{3, 29, 5 * time.Second, "piercing", ""},
	{3, 36, 5 * time.Second, "piercing", ""},
	{3, 44, 5 * time.Second, "piercing", ""},
	{4, 53, 5 * time.Second, "piercing", ""},
	{4, 63, 5 * time.Second, "piercing", ""},
	{4, 75, 5 * time.Second, "piercing", ""},
}

var stormCoilStats = [...]DefenseWeaponStats{
	{2, 90, 15 * time.Second, "shock", economy.ResourceFuel},
	{2, 115, 15 * time.Second, "shock", economy.ResourceFuel},
	{3, 145, 15 * time.Second, "shock", economy.ResourceFuel},
	{3, 180, 15 * time.Second, "shock", economy.ResourceFuel},
	{3, 220, 15 * time.Second, "shock", economy.ResourceFuel},
	{4, 265, 15 * time.Second, "shock", economy.ResourceFuel},
}

func DefenseWeaponLevel(kind building.Type, level int) (DefenseWeaponStats, bool) {
	if level < 1 {
		return DefenseWeaponStats{}, false
	}
	if levels, ok := activeDefenseWeapons[string(kind)]; ok {
		if level > len(levels) {
			return DefenseWeaponStats{}, false
		}
		return levels[level-1], true
	}
	switch kind {
	case building.TypeDefenseCannon:
		stats, ok := CannonLevel(level)
		if !ok {
			return DefenseWeaponStats{}, false
		}
		return DefenseWeaponStats{stats.Range, stats.Damage, 12 * time.Second, "explosive", stats.Ammo}, true
	case building.TypeDefenseBoltThrower:
		if level <= len(boltThrowerStats) {
			return boltThrowerStats[level-1], true
		}
	case building.TypeDefenseStormCoil:
		if level <= len(stormCoilStats) {
			return stormCoilStats[level-1], true
		}
	}
	return DefenseWeaponStats{}, false
}

func IsDefenseWeapon(kind building.Type) bool {
	return kind == building.TypeDefenseCannon || kind == building.TypeDefenseBoltThrower || kind == building.TypeDefenseStormCoil
}
