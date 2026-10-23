package postgres

import (
	"context"
	"database/sql"
	"os"
	"testing"
	"time"

	_ "github.com/lib/pq"

	"real-city/backend/internal/domain/economy"
)

func TestSaveInventoryBatchWithPostgres(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN to run Postgres inventory integration test")
	}
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if _, err := db.ExecContext(ctx, `
		CREATE TEMP TABLE player_inventories (
			player_id text NOT NULL,
			resource text NOT NULL,
			amount bigint NOT NULL,
			updated_at timestamptz NOT NULL,
			PRIMARY KEY (player_id, resource)
		)
	`); err != nil {
		t.Fatal(err)
	}
	repo := NewEconomyRepo(db)
	now := time.Date(2026, 10, 19, 12, 0, 0, 0, time.UTC)
	for _, inventory := range []economy.Inventory{
		{
			PlayerID: "player-1",
			Items: map[economy.ResourceType]int{
				economy.ResourceCoins: 3_000_000_000,
				economy.ResourceWood:  25,
			},
			UpdatedAt: now,
		},
		{
			PlayerID: "player-1",
			Items: map[economy.ResourceType]int{
				economy.ResourceCoins: 3_000_000_000,
				economy.ResourceWood:  20,
				economy.ResourceStone: 15,
			},
			UpdatedAt: now.Add(time.Second),
		},
	} {
		if err := repo.SaveInventory(ctx, inventory); err != nil {
			t.Fatal(err)
		}
	}
	var count int
	var wood int64
	if err := db.QueryRowContext(ctx, `SELECT COUNT(*), MAX(amount) FILTER (WHERE resource = 'wood') FROM player_inventories`).Scan(&count, &wood); err != nil {
		t.Fatal(err)
	}
	if count != 3 || wood != 20 {
		t.Fatalf("inventory rows = %d, wood = %d; want 3 rows and 20 wood", count, wood)
	}
}
