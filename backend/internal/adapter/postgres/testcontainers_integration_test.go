package postgres

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"os/exec"
	"testing"
	"time"

	testcontainers "github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"

	"real-city/backend/internal/adapter/http/middleware"
	redisadapter "real-city/backend/internal/adapter/redis"
)

func TestPostgresRedisContainers(t *testing.T) {
	if os.Getenv("TEST_CONTAINERS") != "1" {
		t.Skip("set TEST_CONTAINERS=1 to start Docker containers")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	postgresContainer, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: testcontainers.ContainerRequest{
			Image: "postgres:16-alpine", ExposedPorts: []string{"5432/tcp"},
			Env:        map[string]string{"POSTGRES_DB": "real_city", "POSTGRES_USER": "real_city", "POSTGRES_PASSWORD": "real_city"},
			WaitingFor: wait.ForListeningPort("5432/tcp").WithStartupTimeout(time.Minute),
		}, Started: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = postgresContainer.Terminate(context.Background()) })
	redisContainer, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: testcontainers.ContainerRequest{
			Image: "redis:7-alpine", ExposedPorts: []string{"6379/tcp"},
			WaitingFor: wait.ForListeningPort("6379/tcp").WithStartupTimeout(time.Minute),
		}, Started: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = redisContainer.Terminate(context.Background()) })
	pgHost, err := postgresContainer.Host(ctx)
	if err != nil {
		t.Fatal(err)
	}
	pgPort, err := postgresContainer.MappedPort(ctx, "5432/tcp")
	if err != nil {
		t.Fatal(err)
	}
	dsn := fmt.Sprintf("postgres://real_city:real_city@%s:%s/real_city?sslmode=disable", pgHost, pgPort.Port())
	migrate := exec.CommandContext(ctx, "go", "run", "./cmd/migrate", "up")
	migrate.Dir = "../../.."
	migrate.Env = append(os.Environ(), "POSTGRES_DSN="+dsn)
	if output, err := migrate.CombinedOutput(); err != nil {
		t.Fatalf("migrations: %v\n%s", err, output)
	}
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	store := NewIdempotencyStore(db)
	response := middleware.IdempotencyRecord{Status: 201, Fingerprint: "payload", Body: []byte(`{"ok":true}`)}
	if err := store.Save(ctx, "container-test", response, time.Minute); err != nil {
		t.Fatal(err)
	}
	got, ok, err := NewIdempotencyStore(db).Get(ctx, "container-test")
	if err != nil || !ok || string(got.Body) != string(response.Body) {
		t.Fatalf("response = %+v, ok=%v, err=%v", got, ok, err)
	}
	unlock, err := store.Lock(ctx, "container-test")
	if err != nil { t.Fatal(err) }
	waiting := make(chan error, 1)
	go func() {
		secondUnlock, err := NewIdempotencyStore(db).Lock(ctx, "container-test")
		if err == nil { secondUnlock() }
		waiting <- err
	}()
	select {
	case err := <-waiting: t.Fatalf("lock was not exclusive: %v", err)
	case <-time.After(50*time.Millisecond):
	}
	unlock()
	select {
	case err := <-waiting: if err != nil { t.Fatal(err) }
	case <-ctx.Done(): t.Fatal("lock wait timed out")
	}
	var balanceVersion int
	if err := db.QueryRowContext(ctx, `SELECT version FROM game_balance_version WHERE singleton=true`).Scan(&balanceVersion); err != nil || balanceVersion != 2 {
		t.Fatalf("balance version = %d, err=%v", balanceVersion, err)
	}
	_, err = db.ExecContext(ctx, `INSERT INTO players(id,email,name,password_hash) VALUES ('container-player','container@example.invalid','ContainerPlayer','hash')`)
	if err != nil {
		t.Fatal(err)
	}
	_, err = db.ExecContext(ctx, `INSERT INTO world_maps(id,name,seed,chunk_size,spawn_radius) VALUES ('container-world','World',1,16,2)`)
	if err != nil {
		t.Fatal(err)
	}
	insert := `INSERT INTO buildings(id,map_id,owner_id,type,name,level,state,health,tile_x,tile_y,footprint_w,footprint_h,started_at) VALUES ($1,'container-world','container-player','oil_well','Well',1,'building',100,1,1,1,1,now())`
	if _, err := db.ExecContext(ctx, insert, "well-1"); err != nil {
		t.Fatal(err)
	}
	if _, err := db.ExecContext(ctx, insert, "well-2"); err == nil {
		t.Fatal("duplicate oil well on one tile was accepted")
	}
	redisHost, err := redisContainer.Host(ctx)
	if err != nil {
		t.Fatal(err)
	}
	redisPort, err := redisContainer.MappedPort(ctx, "6379/tcp")
	if err != nil {
		t.Fatal(err)
	}
	redisClient, err := redisadapter.Dial(ctx, redisHost+":"+redisPort.Port(), "", 0)
	if err != nil {
		t.Fatal(err)
	}
	defer redisClient.Close()
	if err := redisClient.Ping(); err != nil {
		t.Fatal(err)
	}
}
