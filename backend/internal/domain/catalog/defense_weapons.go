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
	{2, 6, 2 * time.Second, "piercing", ""},
	{2, 8, 2 * time.Second, "piercing", ""},
	{3, 10, 2 * time.Second, "piercing", ""},
	{3, 12, 2 * time.Second, "piercing", ""},
	{3, 15, 2 * time.Second, "piercing", ""},
	{4, 18, 2 * time.Second, "piercing", ""},
	{4, 21, 2 * time.Second, "piercing", ""},
	{4, 25, 2 * time.Second, "piercing", ""},
}

var stormCoilStats = [...]DefenseWeaponStats{
	{2, 30, 20 * time.Second, "shock", economy.ResourceFuel},
	{2, 38, 20 * time.Second, "shock", economy.ResourceFuel},
	{3, 48, 20 * time.Second, "shock", economy.ResourceFuel},
	{3, 60, 20 * time.Second, "shock", economy.ResourceFuel},
	{3, 73, 20 * time.Second, "shock", economy.ResourceFuel},
	{4, 88, 20 * time.Second, "shock", economy.ResourceFuel},
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
