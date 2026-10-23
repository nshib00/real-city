package catalog

import "real-city/backend/internal/domain/building"

type BuildingXP struct {
	Completion  int
	Work        int
	Destruction int
}

var buildingXP = map[building.Type][]BuildingXP{
	building.TypeSeedGarden: {
		{12, 2, 80}, {35, 3, 230}, {75, 4, 520}, {130, 5, 950}, {210, 6, 1600},
		{325, 8, 2600}, {470, 10, 4200}, {650, 12, 6800}, {880, 15, 11000}, {1150, 18, 17500},
	},
	building.TypeFlaxField: {
		{40, 7, 215}, {98, 10, 527}, {68, 4, 560}, {118, 5, 1020}, {190, 6, 1700},
		{300, 8, 2850}, {440, 10, 4700}, {620, 12, 7600}, {830, 15, 12200}, {1080, 18, 19000},
	},
	building.TypeGlassWorkshop: {
		{200, 16, 918}, {289, 20, 2011}, {404, 25, 4685}, {695, 32, 9113}, {913, 36, 19322},
		{1210, 41, 45120}, {1788, 48, 71481}, {3012, 57, 130827}, {6557, 70, 297600},
	},
	building.TypeMine: {
		{60, 8, 420}, {115, 10, 870}, {203, 13, 1550}, {346, 16, 2560}, {505, 20, 3910},
		{713, 24, 6700}, {955, 29, 9210}, {1152, 33, 15750}, {1435, 38, 30213}, {1700, 45, 67155},
		{2035, 52, 140560}, {2340, 57, 226700},
	},
	building.TypeRopeYard: {
		{55, 7, 430}, {110, 9, 820}, {190, 12, 1500}, {310, 16, 2750},
		{480, 21, 5100}, {690, 27, 8800}, {930, 34, 14200}, {1220, 42, 23000},
	},
}

func ExperienceForBuilding(kind building.Type, level int) BuildingXP {
	levels := buildingXP[kind]
	if level < 1 || level > len(levels) {
		return BuildingXP{}
	}
	return levels[level-1]
}
