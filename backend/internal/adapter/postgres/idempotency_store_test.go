package postgres

import (
	"context"
	"database/sql"
	"net/http"
	"os"
	"testing"
	"time"

	"real-city/backend/internal/adapter/http/middleware"
)

func TestIdempotencyStoreWithPostgres(t *testing.T) {
	dsn := os.Getenv("TEST_POSTGRES_DSN")
	if dsn == "" {
		t.Skip("set TEST_POSTGRES_DSN and apply migrations")
	}
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	store := NewIdempotencyStore(db)
	key := "test-idempotency-" + time.Now().UTC().Format("20060102150405.000000000")
	defer db.ExecContext(context.Background(), `DELETE FROM http_idempotency_responses WHERE key_hash=$1`, key)
	created, err := store.Begin(ctx, key, "body-v1", time.Hour)
	if err != nil || !created {
		t.Fatalf("begin: created=%v err=%v", created, err)
	}
	if duplicate, err := store.Begin(ctx, key, "body-v1", time.Hour); err != nil || duplicate {
		t.Fatalf("duplicate begin: created=%v err=%v", duplicate, err)
	}
	pending, ok, err := NewIdempotencyStore(db).Get(ctx, key)
	if err != nil || !ok || pending.Status != 0 {
		t.Fatalf("pending = %+v, ok=%v, err=%v", pending, ok, err)
	}
	if _, err := db.ExecContext(ctx, `UPDATE http_idempotency_responses SET expires_at=now()-interval '1 second' WHERE key_hash=$1`, key); err != nil {
		t.Fatal(err)
	}
	if pending, ok, err := store.Get(ctx, key); err != nil || !ok || pending.Status != 0 {
		t.Fatalf("expired pending was lost: %+v ok=%v err=%v", pending, ok, err)
	}
	if duplicate, err := store.Begin(ctx, key, "body-v1", time.Hour); err != nil || duplicate {
		t.Fatalf("expired pending re-executed: created=%v err=%v", duplicate, err)
	}
	first := middleware.IdempotencyRecord{Status: 201, Header: http.Header{"Content-Type": {"application/json"}}, Body: []byte(`{"id":1}`), Fingerprint: "body-v1"}
	if err := store.Save(ctx, key, first, time.Hour); err != nil {
		t.Fatal(err)
	}
	replayed, ok, err := NewIdempotencyStore(db).Get(ctx, key)
	if err != nil || !ok || replayed.Fingerprint != first.Fingerprint || string(replayed.Body) != string(first.Body) {
		t.Fatalf("replayed = %+v, ok=%v, err=%v", replayed, ok, err)
	}
	unlock, err := store.Lock(ctx, key)
	if err != nil {
		t.Fatal(err)
	}
	acquired := make(chan error, 1)
	go func() {
		secondUnlock, err := NewIdempotencyStore(db).Lock(ctx, key)
		if err == nil {
			secondUnlock()
		}
		acquired <- err
	}()
	select {
	case err := <-acquired:
		t.Fatalf("second lock acquired early: %v", err)
	case <-time.After(50 * time.Millisecond):
	}
	unlock()
	select {
	case err := <-acquired:
		if err != nil {
			t.Fatal(err)
		}
	case <-ctx.Done():
		t.Fatal("second lock did not complete")
	}
}
