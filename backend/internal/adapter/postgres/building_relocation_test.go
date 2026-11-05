package postgres

import (
	"context"
	"database/sql"
	"os"
	"testing"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/world"
)

func TestRelocateIfCurrentChecksWrappedOccupiedTiles(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN to run the PostgreSQL relocation test")
	}
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	ctx := context.Background()
	if _, err := db.ExecContext(ctx, `CREATE TEMP TABLE buildings (
		id text PRIMARY KEY, map_id text NOT NULL, type text NOT NULL, state text NOT NULL,
		tile_x integer NOT NULL, tile_y integer NOT NULL, footprint_w integer NOT NULL,
		footprint_h integer NOT NULL, rotation smallint NOT NULL, updated_at timestamptz NOT NULL
	)`); err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC().Truncate(time.Microsecond)
	for _, args := range [][]any{
		{"moving", "test-world", "dugout", "active", 5, 5, 2, 1, 0, now},
		{"blocker", "test-world", "dugout", "active", 0, 5, 1, 1, 0, now},
	} {
		if _, err := db.ExecContext(ctx, `INSERT INTO buildings VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`, args...); err != nil {
			t.Fatal(err)
		}
	}
	previous := building.Building{ID: "moving", MapID: "test-world", Type: building.TypeDugout,
		State: building.StateActive, Tile: world.Coord{X: 5, Y: 5},
		Footprint: building.Footprint{Width: 2, Height: 1}, UpdatedAt: now}
	repo := NewBuildingRepo(db)
	next := previous
	next.Tile = world.Coord{X: world.WorldSize - 1, Y: 5}
	next.UpdatedAt = now.Add(time.Second)
	changed, err := repo.RelocateIfCurrent(ctx, previous, next)
	if err != nil || changed {
		t.Fatalf("cross-seam overlap was accepted: changed=%v err=%v", changed, err)
	}
	next.Tile.X = world.WorldSize - 2
	changed, err = repo.RelocateIfCurrent(ctx, previous, next)
	if err != nil || !changed {
		t.Fatalf("free destination was rejected: changed=%v err=%v", changed, err)
	}
}
