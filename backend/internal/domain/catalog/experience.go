package catalog

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"sync"

	"real-city/backend/internal/domain/building"
)

type BuildingXP struct {
	Completion  int `json:"completion"`
	Work        int `json:"work"`
	Destruction int `json:"destruction"`
}

//go:embed building_xp.json
var buildingXPJSON []byte

var buildingXPOnce sync.Once
var buildingXP map[building.Type]map[int]BuildingXP

func loadBuildingXP() {
	var data struct {
		SchemaVersion int `json:"schema_version"`
		Buildings     map[building.Type][]struct {
			Level int `json:"level"`
			BuildingXP
		} `json:"buildings"`
	}
	if err := json.Unmarshal(buildingXPJSON, &data); err != nil {
		panic(err)
	}
	if data.SchemaVersion != 1 {
		panic("unsupported building XP schema")
	}
	buildingXP = make(map[building.Type]map[int]BuildingXP, len(data.Buildings))
	for kind, rows := range data.Buildings {
		levels := make(map[int]BuildingXP, len(rows))
		for _, row := range rows {
			if _, exists := levels[row.Level]; exists || row.Level < 1 || row.Completion <= 0 || row.Destruction <= 0 || row.Destruction > 500000 || row.Work < 0 {
				panic(fmt.Sprintf("invalid building XP: %s/%d", kind, row.Level))
			}
			levels[row.Level] = row.BuildingXP
		}
		buildingXP[kind] = levels
	}
	// Fail on missing policies when a new building or level is introduced.
	specs := AllBuildings()
	for _, ruin := range RuinSpecs {
		specs = append(specs, ruin)
	}
	if len(specs) != len(buildingXP) {
		panic("building XP types do not match building catalog")
	}
	for _, spec := range specs {
		working := spec.Category == "fields" || spec.Type == building.TypeOilWell
		for _, recipe := range ProductionRecipes {
			working = working || recipe.BuildingType == string(spec.Type)
		}
		levels := spec.UpgradeLevels
		if len(levels) == 0 {
			levels = []BuildingUpgradeLevel{{Level: spec.Level}}
		}
		if len(levels) != len(buildingXP[spec.Type]) {
			panic(fmt.Sprintf("incomplete building XP levels: %s", spec.Type))
		}
		previousDestruction := 0
		for _, level := range levels {
			xp, ok := buildingXP[spec.Type][level.Level]
			if !ok {
				panic(fmt.Sprintf("missing building XP: %s/%d", spec.Type, level.Level))
			}
			if xp.Destruction <= previousDestruction || (working && xp.Work <= 0) {
				panic(fmt.Sprintf("invalid building XP policy: %s/%d", spec.Type, level.Level))
			}
			previousDestruction = xp.Destruction
		}
	}
}

func ValidateBuildingXP() { buildingXPOnce.Do(loadBuildingXP) }

func ExperienceForBuilding(kind building.Type, level int) BuildingXP {
	ValidateBuildingXP()
	return buildingXP[kind][level]
}
