package memory

import (
	"context"
	"encoding/json"
	"strings"
	"testing"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
	"real-city/backend/internal/domain/world"
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

func TestTowerAllySharingDefaultOffRedactedAndRevoked(t *testing.T) {
	ctx := context.Background()
	buildings, social := NewBuildingRepo(), NewSocialRepo()
	joined := time.Date(2026, 11, 5, 10, 0, 0, 0, time.UTC)
	if err := social.Create(ctx, alliance.Alliance{ID: "guild", LeaderID: "owner"}); err != nil {
		t.Fatal(err)
	}
	for _, id := range []string{"owner", "ally"} {
		if err := social.SaveMembership(ctx, alliance.Membership{AllianceID: "guild", PlayerID: player.ID(id), JoinedAt: joined}); err != nil {
			t.Fatal(err)
		}
	}
	for _, item := range []building.Building{
		{ID: "source", MapID: "map", OwnerID: "owner", Type: building.TypeTower, Level: 6, State: building.StateActive, Health: 520, TowerWatchkeeperAssigned: true, Tile: world.Coord{X: 159}},
		{ID: "ally-a", MapID: "map", OwnerID: "ally", Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100, TowerWatchkeeperAssigned: true, Tile: world.Coord{X: 15}},
		{ID: "ally-b", MapID: "map", OwnerID: "ally", Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100, TowerWatchkeeperAssigned: true, Tile: world.Coord{X: 14}},
		{ID: "ally-inactive", MapID: "map", OwnerID: "ally", Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100, Tile: world.Coord{X: 3}},
	} {
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	repo := NewTowerAlertRepo()
	delivered := []toweralert.SharedAlert{}
	repo.SetAllySources(buildings, social, func(id player.ID, alert toweralert.SharedAlert) error {
		if id != "ally" {
			t.Fatalf("recipient %s", id)
		}
		delivered = append(delivered, alert)
		return nil
	})
	now := joined.Add(time.Hour)
	observe := func(monsterID string, at time.Time) {
		t.Helper()
		generation, err := repo.BeginScan(ctx, "map")
		if err != nil {
			t.Fatal(err)
		}
		_, err = repo.Reconcile(ctx, "map", generation, at, []toweralert.Observation{{OwnerID: "owner", TowerID: "source", MonsterID: monsterID, MonsterType: string(monster.TypeForestStalker), TileX: 159, TileY: 0, TargetBuildingID: "secret-home"}})
		if err != nil {
			t.Fatal(err)
		}
	}
	observe("m1", now)
	if len(delivered) != 0 {
		t.Fatalf("default-off delivery: %+v", delivered)
	}
	if err := repo.SetShare(ctx, "source", "owner", "guild", true); err != nil {
		t.Fatal(err)
	}
	observe("m2", now.Add(time.Minute))
	if len(delivered) != 1 {
		t.Fatalf("two ally towers should yield one delivery: %+v", delivered)
	}
	history, err := repo.ListHistoryForPlayer(ctx, "ally", 10, time.Time{}, "")
	if err != nil || len(history) != 1 {
		t.Fatalf("ally history: %+v %v", history, err)
	}
	encoded, err := json.Marshal(history)
	if err != nil {
		t.Fatal(err)
	}
	for _, secret := range []string{"tower_id", "monster_id", "tile_x", "tile_y", "target_building_id", "secret-home", "owner_id"} {
		if strings.Contains(string(encoded), secret) {
			t.Fatalf("ally history leaked %s: %s", secret, encoded)
		}
	}
	if err := repo.SetShare(ctx, "source", "owner", "", false); err != nil {
		t.Fatal(err)
	}
	observe("m3", now.Add(2*time.Minute))
	if len(delivered) != 1 {
		t.Fatalf("delivery after revoke: %+v", delivered)
	}
	if err := repo.SetShare(ctx, "source", "owner", "guild", true); err != nil {
		t.Fatal(err)
	}
	if err := social.DeleteMembership(ctx, "guild", "owner"); err != nil {
		t.Fatal(err)
	}
	if err := social.SaveMembership(ctx, alliance.Membership{AllianceID: "guild", PlayerID: "owner", JoinedAt: joined.Add(3 * time.Hour)}); err != nil {
		t.Fatal(err)
	}
	observe("m4", now.Add(3*time.Minute))
	if len(delivered) != 1 {
		t.Fatalf("old consent survived leave/rejoin: %+v", delivered)
	}
}
