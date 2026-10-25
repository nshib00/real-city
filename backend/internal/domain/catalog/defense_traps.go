package catalog

import "real-city/backend/internal/domain/building"

type DefenseTrapStats struct {
	Damage        int
	MaxCharges    int
	DamageType    string
	Reload        []building.Cost
	SlowsNextStep bool
}

var stakesDamage = [...]int{25, 32, 42, 55, 70, 90}
var resinSnareDamage = [...]int{12, 18, 26, 36}

func DefenseTrapLevel(kind building.Type, level int) (DefenseTrapStats, bool) {
	if level < 1 {
		return DefenseTrapStats{}, false
	}
	switch kind {
	case building.TypeDefenseStakes:
		if level <= len(stakesDamage) {
			return DefenseTrapStats{stakesDamage[level-1], 3, "piercing", []building.Cost{{Resource: "wood", Amount: 2}, {Resource: "rope", Amount: 1}}, false}, true
		}
	case building.TypeDefenseResinSnare:
		if level <= len(resinSnareDamage) {
			return DefenseTrapStats{resinSnareDamage[level-1], 2, "basic", []building.Cost{{Resource: "resin", Amount: 2}}, true}, true
		}
	}
	return DefenseTrapStats{}, false
}
