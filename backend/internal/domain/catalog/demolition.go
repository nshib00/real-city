package catalog

import "real-city/backend/internal/domain/building"

func DemolitionRefundCoins(kind building.Type, level int) int {
	if kind == building.TypeOilWell {
		return demolitionSpentCoins(kind, level, map[building.Type]bool{}) / 2
	}
	return demolitionSpentCoins(kind, level, map[building.Type]bool{}) / 5
}

func demolitionSpentCoins(kind building.Type, level int, visited map[building.Type]bool) int {
	spec, ok := GetBuilding(kind)
	if !ok || visited[kind] {
		return 0
	}
	visited[kind] = true
	spent := 0
	if len(spec.UpgradeLevels) == 0 {
		spent += coinCost(spec.Cost)
	} else {
		for _, upgrade := range spec.UpgradeLevels {
			if upgrade.Level <= level {
				spent += coinCost(upgrade.Cost)
			}
		}
	}
	for previousKind, previous := range Buildings {
		if previousKind == kind {
			continue
		}
		transitions := false
		for _, upgrade := range previous.UpgradeLevels {
			if upgrade.NextType == kind {
				transitions = true
				break
			}
		}
		if !transitions {
			for _, nextKind := range previous.UpgradeTo {
				if nextKind == kind {
					transitions = true
					break
				}
			}
		}
		if transitions {
			previousLevel := previous.Level
			if count := len(previous.UpgradeLevels); count > 0 {
				previousLevel = previous.UpgradeLevels[count-1].Level
			}
			spent += demolitionSpentCoins(previousKind, previousLevel, visited)
			break
		}
	}
	return spent
}

func coinCost(cost []building.Cost) int {
	coins := 0
	for _, item := range cost {
		if item.Resource == "coins" {
			coins += item.Amount
		}
	}
	return coins
}
