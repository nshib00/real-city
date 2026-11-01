package dto

import (
	"testing"

	"real-city/backend/internal/domain/catalog"
)

func TestFullCatalogDTOExposesEveryLevel(t *testing.T) {
	source := catalog.AllBuildings()
	api := BuildingCatalog(source)
	if len(source) == 0 || len(api) != len(source) {
		t.Fatalf("source=%d api=%d", len(source), len(api))
	}
	for index, spec := range source {
		item := api[index]
		if item.Type != string(spec.Type) || item.Name != spec.Name || item.Health != spec.Health || item.FirstLevel != catalog.CanPlaceDirectly(spec.Type) {
			t.Fatalf("API metadata differs for %s: %+v", spec.Type, item)
		}
		expectedLevels := len(spec.UpgradeLevels)
		if expectedLevels == 0 {
			expectedLevels = 1
		}
		if len(item.UpgradeLevels) != expectedLevels {
			t.Fatalf("%s: %d levels, want %d", spec.Type, len(item.UpgradeLevels), expectedLevels)
		}
		for levelIndex, level := range item.UpgradeLevels {
			if len(spec.UpgradeLevels) == 0 {
				if level.Level != spec.Level || level.Health != spec.Health || level.BuildSeconds != int(spec.BuildDuration.Seconds()) {
					t.Fatalf("%s: base level differs", spec.Type)
				}
				continue
			}
			expected := spec.UpgradeLevels[levelIndex]
			if level.Level != expected.Level || level.Health != expected.Health || level.BuildSeconds != int(expected.BuildDuration.Seconds()) || len(level.Cost) != len(expected.Cost) {
				t.Fatalf("%s L%d differs: %+v", spec.Type, expected.Level, level)
			}
		}
	}
}
