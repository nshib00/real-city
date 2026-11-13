package catalog

import "real-city/backend/internal/domain/economy"

type CannonStats struct {
	Range  int
	Damage int
	Ammo   economy.ResourceType
}

var cannonStats = [...]CannonStats{
	{Range: 2, Damage: 18, Ammo: economy.ResourceStone},
	{Range: 2, Damage: 23, Ammo: economy.ResourceStone},
	{Range: 3, Damage: 27, Ammo: economy.ResourceStone},
	{Range: 3, Damage: 33, Ammo: economy.ResourceStone},
	{Range: 3, Damage: 41, Ammo: economy.ResourceStone},
	{Range: 4, Damage: 49, Ammo: economy.ResourceStone},
	{Range: 4, Damage: 60, Ammo: economy.ResourceExplosives},
	{Range: 4, Damage: 72, Ammo: economy.ResourceExplosives},
	{Range: 5, Damage: 85, Ammo: economy.ResourceExplosives},
	{Range: 5, Damage: 100, Ammo: economy.ResourceExplosives},
	{Range: 5, Damage: 117, Ammo: economy.ResourceExplosives},
	{Range: 6, Damage: 137, Ammo: economy.ResourceExplosives},
}

func CannonLevel(level int) (CannonStats, bool) {
	if len(activeCannons) > 0 {
		if level < 1 || level > len(activeCannons) {
			return CannonStats{}, false
		}
		return activeCannons[level-1], true
	}
	if level < 1 || level > len(cannonStats) {
		return CannonStats{}, false
	}
	return cannonStats[level-1], true
}
