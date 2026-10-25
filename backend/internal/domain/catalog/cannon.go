package catalog

import "real-city/backend/internal/domain/economy"

type CannonStats struct {
	Range  int
	Damage int
	Ammo   economy.ResourceType
}

var cannonStats = [...]CannonStats{
	{Range: 2, Damage: 55, Ammo: economy.ResourceStone},
	{Range: 2, Damage: 68, Ammo: economy.ResourceStone},
	{Range: 3, Damage: 82, Ammo: economy.ResourceStone},
	{Range: 3, Damage: 100, Ammo: economy.ResourceStone},
	{Range: 3, Damage: 122, Ammo: economy.ResourceStone},
	{Range: 4, Damage: 148, Ammo: economy.ResourceStone},
	{Range: 4, Damage: 180, Ammo: economy.ResourceExplosives},
	{Range: 4, Damage: 215, Ammo: economy.ResourceExplosives},
	{Range: 5, Damage: 255, Ammo: economy.ResourceExplosives},
	{Range: 5, Damage: 300, Ammo: economy.ResourceExplosives},
	{Range: 5, Damage: 350, Ammo: economy.ResourceExplosives},
	{Range: 6, Damage: 410, Ammo: economy.ResourceExplosives},
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
