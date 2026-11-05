package redis

import (
	"context"
	"os"
	"testing"
	"time"

	testcontainers "github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
)

func TestGameCacheRedisRoundTrip(t *testing.T) {
	if os.Getenv("TEST_CONTAINERS") != "1" {
		t.Skip("set TEST_CONTAINERS=1 to start Docker containers")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: testcontainers.ContainerRequest{
			Image: "redis:7-alpine", ExposedPorts: []string{"6379/tcp"},
			WaitingFor: wait.ForListeningPort("6379/tcp").WithStartupTimeout(time.Minute),
		}, Started: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = container.Terminate(context.Background()) })
	host, err := container.Host(ctx)
	if err != nil {
		t.Fatal(err)
	}
	port, err := container.MappedPort(ctx, "6379/tcp")
	if err != nil {
		t.Fatal(err)
	}
	cache := &GameCache{Addr: host + ":" + port.Port()}
	if _, hit, err := cache.Get(ctx, "game-cache-test"); err != nil || hit {
		t.Fatalf("initial get hit=%v err=%v", hit, err)
	}
	if err := cache.Set(ctx, "game-cache-test", []byte("snapshot"), 2*time.Second); err != nil {
		t.Fatal(err)
	}
	if value, hit, err := cache.Get(ctx, "game-cache-test"); err != nil || !hit || string(value) != "snapshot" {
		t.Fatalf("get value=%q hit=%v err=%v", value, hit, err)
	}
	if values, err := cache.GetMany(ctx, []string{"game-cache-test", "game-cache-absent"}); err != nil || string(values["game-cache-test"]) != "snapshot" || len(values) != 1 {
		t.Fatalf("MGET values=%v err=%v", values, err)
	}
	if err := cache.Delete(ctx, "game-cache-test"); err != nil {
		t.Fatal(err)
	}
	if _, hit, err := cache.Get(ctx, "game-cache-test"); err != nil || hit {
		t.Fatalf("after delete hit=%v err=%v", hit, err)
	}
}
