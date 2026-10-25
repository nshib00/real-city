package redis

import (
	"context"
	"os"
	"testing"
	"time"
)

func TestRedisConnectionWithServer(t *testing.T) {
	addr := os.Getenv("TEST_REDIS_ADDR")
	if addr == "" {
		t.Skip("set TEST_REDIS_ADDR to run Redis integration test")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	client, err := Dial(ctx, addr, "", 1)
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	if err := client.Ping(); err != nil {
		t.Fatal(err)
	}
	if key := client.Key(NamespaceIdempotency, "integration"); key != "real-city:idempotency:integration" {
		t.Fatalf("key = %q", key)
	}
}
