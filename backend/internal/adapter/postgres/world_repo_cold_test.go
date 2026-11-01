package postgres

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
)

func TestBulkColdChunksInIsolatedSchema(t *testing.T) {
	dsn := os.Getenv("REAL_CITY_PERF_TEST_DSN")
	if dsn == "" {
		t.Skip("set REAL_CITY_PERF_TEST_DSN to an isolated schema")
	}
	if !strings.Contains(dsn, "search_path=perf_") {
		t.Fatal("cold chunk test requires an isolated perf_ schema")
	}
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(5)
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	mapID := fmt.Sprintf("perf-cold-%d", time.Now().UnixNano())
	repo := NewWorldRepo(db)
	repo.generator = worldgen.New(mapID, 20260727, 10)
	coords := make([]world.ChunkCoord, 0, 25)
	for y := range 5 {
		for x := range 5 {
			coords = append(coords, world.ChunkCoord{X: x, Y: y})
		}
	}
	started := time.Now()
	chunks, err := repo.GetOrCreateChunks(ctx, mapID, coords)
	if err != nil || len(chunks) != len(coords) {
		t.Fatalf("cold chunks=%d err=%v", len(chunks), err)
	}
	for _, chunk := range chunks {
		if len(chunk.Tiles) != world.ChunkSize*world.ChunkSize {
			t.Fatalf("chunk %+v has %d tiles", chunk.Coord, len(chunk.Tiles))
		}
	}
	t.Logf("25 cold chunks in %s", time.Since(started))
}
