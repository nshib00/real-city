package catalog

import "real-city/backend/internal/domain/building"

type DefenseBaseStats struct {
	Slots        int
	PatrolRadius int
	StaffRole    string
}

var defenseBaseProgression = [...]DefenseBaseStats{
	{2, 3, ""}, {3, 3, ""}, {4, 4, ""}, {5, 4, ""}, {6, 5, ""},
}

func DefenseBaseLevel(kind building.Type, level int) (DefenseBaseStats, bool) {
	if level < 1 || level > len(defenseBaseProgression) {
		return DefenseBaseStats{}, false
	}
	stats := defenseBaseProgression[level-1]
	switch kind {
	case building.TypeDefenseAutomatonBay:
		stats.StaffRole = "mechanic"
	case building.TypeDefenseGuardianEnclosure:
		stats.StaffRole = "keeper"
	default:
		return DefenseBaseStats{}, false
	}
	return stats, true
}
