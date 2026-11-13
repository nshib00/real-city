package postgres

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
)

func TestTowerSharedPendingPrivacyRevokeAndMembershipEpoch(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN to a database migrated through 000058")
	}
	ctx := context.Background()
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	suffix := time.Now().UnixNano()
	mapID, owner, ally, guild := fmt.Sprintf("share_map_%d", suffix), fmt.Sprintf("share_owner_%d", suffix), fmt.Sprintf("share_ally_%d", suffix), fmt.Sprintf("share_guild_%d", suffix)
	sourceID, targetID := fmt.Sprintf("share_source_%d", suffix), fmt.Sprintf("share_target_%d", suffix)
	defer func() {
		_, _ = db.ExecContext(ctx, `DELETE FROM outbox_events WHERE aggregate_id IN (SELECT id FROM tower_alert_incidents WHERE map_id=$1)`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_recipients WHERE incident_id IN (SELECT id FROM tower_alert_incidents WHERE map_id=$1)`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_incidents WHERE map_id=$1`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_state WHERE map_id=$1`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_scans WHERE map_id=$1`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM buildings WHERE map_id=$1`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM alliances WHERE id=$1`, guild)
		_, _ = db.ExecContext(ctx, `DELETE FROM players WHERE id IN ($1,$2)`, owner, ally)
		_, _ = db.ExecContext(ctx, `DELETE FROM world_maps WHERE id=$1`, mapID)
	}()
	if _, err := db.ExecContext(ctx, `INSERT INTO world_maps(id,name,seed,chunk_size,spawn_radius) VALUES($1,$1,1,32,3)`, mapID); err != nil {
		t.Fatal(err)
	}
	for _, id := range []string{owner, ally} {
		if _, err := db.ExecContext(ctx, `INSERT INTO players(id,email,name,password_hash) VALUES($1,$2,$1,'test')`, id, id+"@example.invalid"); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := db.ExecContext(ctx, `INSERT INTO alliances(id,name,leader_id) VALUES($1,$1,$2)`, guild, owner); err != nil {
		t.Fatal(err)
	}
	joined := time.Date(2026, 11, 5, 10, 0, 0, 0, time.UTC)
	for _, member := range []struct{ id, role string }{{owner, "leader"}, {ally, "member"}} {
		if _, err := db.ExecContext(ctx, `INSERT INTO alliance_members(alliance_id,player_id,role,joined_at) VALUES($1,$2,$3,$4)`, guild, member.id, member.role, joined); err != nil {
			t.Fatal(err)
		}
	}
	for _, b := range []struct {
		id, owner        string
		level, health, x int
	}{{sourceID, owner, 6, 520, 159}, {targetID, ally, 1, 100, 15}} {
		if _, err := db.ExecContext(ctx, `INSERT INTO buildings(id,map_id,owner_id,type,name,level,state,health,tile_x,tile_y,started_at,tower_watchkeeper_assigned) VALUES($1,$2,$3,'tower','Tower',$4,'active',$5,$6,0,$7,TRUE)`, b.id, mapID, b.owner, b.level, b.health, b.x, joined); err != nil {
			t.Fatal(err)
		}
	}
	repo := NewTowerAlertRepo(db)
	if err := repo.SetShare(ctx, sourceID, player.ID(owner), alliance.ID(guild), true); err != nil {
		t.Fatal(err)
	}
	create := func(monster string) (string, string) {
		t.Helper()
		generation, err := repo.BeginScan(ctx, mapID)
		if err != nil {
			t.Fatal(err)
		}
		items, err := repo.Reconcile(ctx, mapID, generation, joined.Add(time.Hour), []toweralert.Observation{{OwnerID: player.ID(owner), TowerID: sourceID, MonsterID: monster, MonsterType: "forest_stalker", TileX: 159, TileY: 0, TargetBuildingID: "private-target"}})
		if err != nil || len(items) != 1 {
			t.Fatalf("incident %s: %+v %v", monster, items, err)
		}
		return items[0].IncidentID, "tower-share:" + items[0].IncidentID + ":" + ally
	}
	_, pendingID := create("monster-before-revoke")
	assertSharedCount := func(want int) {
		t.Helper()
		items, err := repo.ListHistoryForPlayer(ctx, player.ID(ally), 10, time.Time{}, "")
		if err != nil || len(items) != want {
			t.Fatalf("shared history count=%d want=%d err=%v", len(items), want, err)
		}
		if want > 0 {
			data, err := json.Marshal(items)
			if err != nil {
				t.Fatal(err)
			}
			for _, secret := range []string{"tower_id", "monster_id", "tile_x", "tile_y", "target_building_id", "private-target", "owner_id"} {
				if strings.Contains(string(data), secret) {
					t.Fatalf("history leaked %s: %s", secret, data)
				}
			}
		}
	}
	assertSharedCount(0)
	if err := repo.SetShare(ctx, sourceID, player.ID(owner), "", false); err != nil {
		t.Fatal(err)
	}
	called := false
	if published, err := repo.PublishSharedIfEligible(ctx, pendingID, func() error { called = true; return nil }); err != nil || published || called {
		t.Fatalf("revoked pending published=%v called=%v err=%v", published, called, err)
	}
	assertSharedCount(0)
	if err := repo.SetShare(ctx, sourceID, player.ID(owner), alliance.ID(guild), true); err != nil {
		t.Fatal(err)
	}
	_, deliverID := create("monster-delivered")
	var payload []byte
	if err := db.QueryRowContext(ctx, `SELECT payload FROM outbox_events WHERE id=$1 AND player_id=$2 AND chunk_id='' AND alliance=''`, deliverID, ally).Scan(&payload); err != nil {
		t.Fatal(err)
	}
	for _, secret := range []string{"tower_id", "monster_id", "tile_x", "tile_y", "target_building_id", "private-target", "owner_id"} {
		if strings.Contains(string(payload), secret) {
			t.Fatalf("outbox leaked %s: %s", secret, payload)
		}
	}
	if published, err := repo.PublishSharedIfEligible(ctx, deliverID, func() error { called = true; return nil }); err != nil || !published {
		t.Fatalf("eligible pending published=%v err=%v", published, err)
	}
	assertSharedCount(1)
	if err := repo.SetShare(ctx, sourceID, player.ID(owner), "", false); err != nil {
		t.Fatal(err)
	}
	assertSharedCount(1)
	if err := repo.SetShare(ctx, sourceID, player.ID(owner), alliance.ID(guild), true); err != nil {
		t.Fatal(err)
	}
	_, raceID := create("monster-race")
	entered, release := make(chan struct{}), make(chan struct{})
	guardDone := make(chan error, 1)
	go func() {
		published, err := repo.PublishSharedIfEligible(ctx, raceID, func() error { close(entered); <-release; return nil })
		if err == nil && !published { err = fmt.Errorf("guard denied eligible race event") }
		guardDone <- err
	}()
	<-entered
	revokeDone := make(chan error, 1)
	go func() { revokeDone <- repo.SetShare(ctx, sourceID, player.ID(owner), "", false) }()
	select {
	case err := <-revokeDone:
		t.Fatalf("revoke crossed in-flight dispatch: %v", err)
	case <-time.After(50 * time.Millisecond):
	}
	close(release)
	if err := <-guardDone; err != nil { t.Fatal(err) }
	if err := <-revokeDone; err != nil { t.Fatal(err) }
	assertSharedCount(2)
	if err := repo.SetShare(ctx, sourceID, player.ID(owner), alliance.ID(guild), true); err != nil { t.Fatal(err) }
	_, rejoinID := create("monster-rejoin")
	if _, err := db.ExecContext(ctx, `DELETE FROM alliance_members WHERE player_id=$1`, ally); err != nil {
		t.Fatal(err)
	}
	if _, err := db.ExecContext(ctx, `INSERT INTO alliance_members(alliance_id,player_id,role,joined_at) VALUES($1,$2,'member',$3)`, guild, ally, joined.Add(2*time.Hour)); err != nil {
		t.Fatal(err)
	}
	if published, err := repo.PublishSharedIfEligible(ctx, rejoinID, func() error { t.Fatal("left/rejoined recipient published"); return nil }); err != nil || published {
		t.Fatalf("rejoin published=%v err=%v", published, err)
	}
	assertSharedCount(2)
}
