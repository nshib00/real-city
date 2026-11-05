package service

import (
	"testing"
	"time"

	"real-city/backend/internal/domain/building"
)

func TestTowerUpgradeLevelsFollowRuntimeCatalog(t *testing.T) {
	coins := []int{36000, 60000, 100000, 160000, 240000}
	durations := []time.Duration{8, 15, 25, 40, 60}
	for current := 1; current < 6; current++ {
		next, ok := nextUpgradeTo(building.Building{Type: building.TypeTower, Level: current}, "")
		if !ok || next.Type != building.TypeTower || next.Level != current+1 {
			t.Fatalf("tower level %d has no next upgrade", current)
		}
		if next.BuildDuration != durations[current-1]*time.Minute || len(next.Cost) == 0 || next.Cost[0].Resource != "coins" || next.Cost[0].Amount != coins[current-1] {
			t.Fatalf("tower level %d upgrade differs from catalog: %+v", current+1, next)
		}
	}
	if _, ok := nextUpgradeTo(building.Building{Type: building.TypeTower, Level: 6}, ""); ok {
		t.Fatal("tower level 6 must be final")
	}
}
