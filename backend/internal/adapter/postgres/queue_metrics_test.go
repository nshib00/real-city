package postgres

import (
	"context"
	"database/sql"
	"os"
	"testing"
	"time"

	_ "github.com/lib/pq"
)

// Uses temporary tables on a single dedicated connection so it cannot change game data.
func TestCollectQueuesAndPoolWaitWithPostgres(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN to run Postgres observability integration test")
	}
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		t.Fatal(err)
	}
	for _, statement := range []string{
		`CREATE TEMP TABLE game_actions (status text, due_at timestamptz)`,
		`CREATE TEMP TABLE outbox_events (status text, next_attempt_at timestamptz)`,
		`CREATE TEMP TABLE buildings (state text, completes_at timestamptz)`,
		`CREATE TEMP TABLE production_jobs (state text, completes_at timestamptz)`,
		`INSERT INTO game_actions VALUES ('pending', now() - interval '10 seconds'), ('pending', now() + interval '1 hour')`,
		`INSERT INTO outbox_events VALUES ('pending', now() - interval '20 seconds'), ('dead', now() - interval '1 minute')`,
	} {
		if _, err := db.ExecContext(ctx, statement); err != nil {
			t.Fatalf("setup: %v", err)
		}
	}
	queue, err := CollectQueues(ctx, db, time.Now().UTC())
	if err != nil {
		t.Fatal(err)
	}
	if queue["actions"].Pending != 2 || queue["actions"].Due != 1 || queue["actions"].OldestDueAge < 9 || queue["outbox"].Dead != 1 || queue["outbox"].Due != 1 {
		t.Fatalf("unexpected queue snapshot: %+v", queue)
	}
	conn, err := db.Conn(ctx)
	if err != nil {
		t.Fatal(err)
	}
	finished := make(chan error, 1)
	go func() {
		_, queryErr := db.ExecContext(ctx, `SELECT pg_sleep(0.05)`)
		finished <- queryErr
	}()
	time.Sleep(20 * time.Millisecond)
	if err := conn.Close(); err != nil {
		t.Fatal(err)
	}
	if err := <-finished; err != nil {
		t.Fatal(err)
	}
	if stats := db.Stats(); stats.WaitCount < 1 || stats.WaitDuration <= 0 {
		t.Fatalf("pool wait was not recorded: %+v", stats)
	}
}
