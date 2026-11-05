package memory

import (
	"context"
	"testing"
	"time"

	"real-city/backend/internal/domain/toweralert"
)

func TestTowerAlertRepoEpisodesAndStaleScans(t *testing.T) {
	ctx := context.Background()
	repo := NewTowerAlertRepo()
	now := time.Date(2026, 11, 5, 12, 0, 0, 0, time.UTC)
	observation := toweralert.Observation{OwnerID: "owner", TowerID: "tower", MonsterID: "monster", MonsterType: "forest_stalker"}
	first, _ := repo.BeginScan(ctx, "map")
	second, _ := repo.BeginScan(ctx, "map")
	created, err := repo.Reconcile(ctx, "map", second, now, []toweralert.Observation{observation})
	if err != nil || len(created) != 1 || created[0].IncidentID == "" {
		t.Fatalf("first incident: %+v %v", created, err)
	}
	firstID := created[0].IncidentID
	if stale, err := repo.Reconcile(ctx, "map", first, now, nil); err != nil || len(stale) != 0 {
		t.Fatalf("stale scan: %+v %v", stale, err)
	}
	third, _ := repo.BeginScan(ctx, "map")
	if got, _ := repo.Reconcile(ctx, "map", third, now.Add(5*time.Second), []toweralert.Observation{observation}); len(got) != 0 {
		t.Fatalf("still inside: %+v", got)
	}
	fourth, _ := repo.BeginScan(ctx, "map")
	_, _ = repo.Reconcile(ctx, "map", fourth, now.Add(10*time.Second), nil)
	fifth, _ := repo.BeginScan(ctx, "map")
	if got, _ := repo.Reconcile(ctx, "map", fifth, now.Add(15*time.Second), []toweralert.Observation{observation}); len(got) != 0 {
		t.Fatalf("reentry during cooldown: %+v", got)
	}
	sixth, _ := repo.BeginScan(ctx, "map")
	_, _ = repo.Reconcile(ctx, "map", sixth, now.Add(time.Minute), nil)
	seventh, _ := repo.BeginScan(ctx, "map")
	created, err = repo.Reconcile(ctx, "map", seventh, now.Add(time.Minute+5*time.Second), []toweralert.Observation{observation})
	if err != nil || len(created) != 1 || created[0].IncidentID == firstID {
		t.Fatalf("second episode: %+v %v", created, err)
	}
	owner, _ := repo.ListForPlayer(ctx, "owner", 50, time.Time{}, "")
	other, _ := repo.ListForPlayer(ctx, "other", 50, time.Time{}, "")
	if len(owner) != 2 || len(other) != 0 || owner[0].IncidentID == owner[1].IncidentID {
		t.Fatalf("private persistent history: owner=%+v other=%+v", owner, other)
	}
}
