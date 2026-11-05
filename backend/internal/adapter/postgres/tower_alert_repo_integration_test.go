package postgres

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"testing"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
)

func TestTowerAlertAtomicHistoryAndOutbox(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN to a migrated test database")
	}
	ctx := context.Background()
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	suffix := time.Now().UnixNano()
	mapID := fmt.Sprintf("tower_alert_test_%d", suffix)
	owner := player.ID(fmt.Sprintf("tower_alert_owner_%d", suffix))
	repo := NewTowerAlertRepo(db)
	defer func() {
		_, _ = db.ExecContext(ctx, `DELETE FROM outbox_events WHERE aggregate_id IN (SELECT id FROM tower_alert_incidents WHERE map_id=$1)`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_recipients WHERE incident_id IN (SELECT id FROM tower_alert_incidents WHERE map_id=$1)`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_incidents WHERE map_id=$1`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_state WHERE map_id=$1`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM tower_alert_scans WHERE map_id=$1`, mapID)
		_, _ = db.ExecContext(ctx, `DELETE FROM players WHERE id=$1`, owner)
	}()
	generation, err := repo.BeginScan(ctx, mapID)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Date(2026, 11, 5, 12, 0, 0, 0, time.UTC)
	observation := toweralert.Observation{OwnerID: owner, TowerID: "tower", MonsterID: "monster", MonsterType: "forest_stalker"}
	if _, err := repo.Reconcile(ctx, mapID, generation, now, []toweralert.Observation{observation}); err == nil {
		t.Fatal("missing recipient player should roll back the incident")
	}
	var count int
	if err := db.QueryRowContext(ctx, `SELECT count(*) FROM tower_alert_incidents WHERE map_id=$1`, mapID).Scan(&count); err != nil || count != 0 {
		t.Fatalf("rolled-back incident count=%d err=%v", count, err)
	}
	if _, err := db.ExecContext(ctx, `INSERT INTO players(id,email,name,password_hash) VALUES($1,$2,$1,'test')`, owner, string(owner)+"@example.invalid"); err != nil {
		t.Fatal(err)
	}
	created, err := repo.Reconcile(ctx, mapID, generation, now, []toweralert.Observation{observation})
	if err != nil || len(created) != 1 {
		t.Fatalf("retry: %+v %v", created, err)
	}
	if err := db.QueryRowContext(ctx, `SELECT count(*) FROM outbox_events WHERE id=$1 AND player_id=$2 AND chunk_id='' AND alliance=''`, "tower-alert:"+created[0].IncidentID, owner).Scan(&count); err != nil || count != 1 {
		t.Fatalf("private outbox count=%d err=%v", count, err)
	}
	if duplicate, err := repo.Reconcile(ctx, mapID, generation, now, []toweralert.Observation{observation}); err != nil || len(duplicate) != 0 {
		t.Fatalf("duplicate generation: %+v %v", duplicate, err)
	}
	items, err := NewTowerAlertRepo(db).ListForPlayer(ctx, owner, 10, time.Time{}, "")
	if err != nil || len(items) != 1 || items[0].IncidentID != created[0].IncidentID {
		t.Fatalf("history: %+v %v", items, err)
	}
	other, err := repo.ListForPlayer(ctx, "other", 10, time.Time{}, "")
	if err != nil || len(other) != 0 {
		t.Fatalf("other history: %+v %v", other, err)
	}
}
