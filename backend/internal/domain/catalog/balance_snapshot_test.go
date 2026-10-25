package catalog

import (
	"encoding/json"
	"os"
	"testing"

	"real-city/backend/internal/domain/building"
)

type snapshotCost struct {
	Resource string `json:"resource"`
	Amount   int    `json:"amount"`
}
type snapshotLevel struct {
	Level        int            `json:"level"`
	BuildSeconds int            `json:"buildSeconds"`
	Population   int            `json:"population"`
	Health       int            `json:"health"`
	Cost         []snapshotCost `json:"cost"`
}
type snapshotBuilding struct {
	Type      string `json:"type"`
	Name      string `json:"name"`
	Category  string `json:"category"`
	Footprint struct {
		Width  int `json:"width"`
		Height int `json:"height"`
	} `json:"footprint"`
	Level         int             `json:"level"`
	BuildSeconds  int             `json:"buildSeconds"`
	Population    int             `json:"population"`
	Health        int             `json:"health"`
	Cost          []snapshotCost  `json:"cost"`
	UpgradeTo     []string        `json:"upgradeTo"`
	FirstLevel    bool            `json:"firstLevel"`
	UpgradeLevels []snapshotLevel `json:"upgradeLevels"`
}

func TestWallVariantsCanBePlacedDirectly(t *testing.T) {
	for _, wall := range []struct {
		typeID building.Type
		level  int
	}{
		{building.TypeWoodenWall, 1},
		{building.TypeStoneWall, 4},
		{building.TypeConcreteWall, 8},
		{building.TypeModernWall, 11},
	} {
		if !CanPlaceDirectly(wall.typeID) {
			t.Errorf("%s cannot be placed directly", wall.typeID)
		}
		spec, ok := GetBuilding(wall.typeID)
		if !ok || spec.Level != wall.level {
			t.Errorf("%s: initial level = %d, want %d", wall.typeID, spec.Level, wall.level)
		}
	}
}

func TestBuildingBalanceSnapshotMatchesRuntime(t *testing.T) {
	raw, err := os.ReadFile("../../../../data/buildings/catalog-v2.json")
	if err != nil {
		t.Fatal(err)
	}
	var snapshot struct {
		SchemaVersion  int                `json:"schema_version"`
		BalanceVersion int                `json:"balance_version"`
		Buildings      []snapshotBuilding `json:"buildings"`
	}
	if err := json.Unmarshal(raw, &snapshot); err != nil {
		t.Fatal(err)
	}
	if snapshot.SchemaVersion != 1 || snapshot.BalanceVersion != BalanceVersion {
		t.Fatalf("unsupported snapshot: schema=%d balance=%d", snapshot.SchemaVersion, snapshot.BalanceVersion)
	}
	if len(snapshot.Buildings) != len(Buildings) {
		t.Fatalf("snapshot=%d runtime=%d", len(snapshot.Buildings), len(Buildings))
	}
	firstLevel := make(map[string]bool)
	for _, spec := range FirstLevelBuildings() {
		firstLevel[string(spec.Type)] = true
	}
	for _, item := range snapshot.Buildings {
		if firstLevel[item.Type] != item.FirstLevel {
			t.Errorf("availability differs for %s", item.Type)
		}
		spec, ok := GetBuilding(building.Type(item.Type))
		if !ok {
			t.Errorf("missing %s", item.Type)
			continue
		}
		if spec.Name != item.Name || spec.Category != item.Category || spec.Footprint.Width != item.Footprint.Width || spec.Footprint.Height != item.Footprint.Height {
			t.Errorf("metadata differs for %s", item.Type)
		}
		if len(spec.UpgradeTo) != len(item.UpgradeTo) {
			t.Errorf("upgrade paths differ for %s", item.Type)
		} else {
			for index, next := range spec.UpgradeTo {
				if string(next) != item.UpgradeTo[index] {
					t.Errorf("upgrade path differs for %s", item.Type)
				}
			}
		}
		levels := item.UpgradeLevels
		if len(levels) == 0 {
			levels = []snapshotLevel{{Level: item.Level, BuildSeconds: item.BuildSeconds, Population: item.Population, Health: item.Health, Cost: item.Cost}}
		}
		if len(spec.UpgradeLevels) > 0 && len(levels) != len(spec.UpgradeLevels) {
			t.Errorf("levels differ for %s", item.Type)
			continue
		}
		for _, level := range levels {
			actual := BuildingUpgradeLevel{Level: spec.Level, BuildDuration: spec.BuildDuration, Population: spec.Population, Health: spec.Health, Cost: spec.Cost}
			if len(spec.UpgradeLevels) > 0 {
				found := false
				for _, candidate := range spec.UpgradeLevels {
					if candidate.Level == level.Level {
						actual = candidate
						found = true
						break
					}
				}
				if !found {
					t.Errorf("missing %s L%d", item.Type, level.Level)
					continue
				}
			}
			if actual.Level != level.Level || int(actual.BuildDuration.Seconds()) != level.BuildSeconds || actual.Population != level.Population || actual.Health != level.Health {
				t.Errorf("stats differ for %s L%d: runtime=%d/%d/%d/%d snapshot=%d/%d/%d/%d", item.Type, level.Level, actual.Level, int(actual.BuildDuration.Seconds()), actual.Population, actual.Health, level.Level, level.BuildSeconds, level.Population, level.Health)
			}
			wantCost := make(map[string]int, len(level.Cost))
			for _, cost := range level.Cost {
				wantCost[cost.Resource] = cost.Amount
			}
			if len(actual.Cost) != len(wantCost) {
				t.Errorf("cost count differs for %s L%d", item.Type, level.Level)
				continue
			}
			for _, cost := range actual.Cost {
				if wantCost[cost.Resource] != cost.Amount {
					t.Errorf("cost differs for %s L%d %s", item.Type, level.Level, cost.Resource)
				}
			}
		}
	}
}
