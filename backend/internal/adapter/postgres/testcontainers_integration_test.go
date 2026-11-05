package postgres

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
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
	if err != nil {
		t.Fatal(err)
	}
	waiting := make(chan error, 1)
	go func() {
		secondUnlock, err := NewIdempotencyStore(db).Lock(ctx, "container-test")
		if err == nil {
			secondUnlock()
		}
		waiting <- err
	}()
	select {
	case err := <-waiting:
		t.Fatalf("lock was not exclusive: %v", err)
	case <-time.After(50 * time.Millisecond):
	}
	unlock()
	select {
	case err := <-waiting:
		if err != nil {
			t.Fatal(err)
		}
	case <-ctx.Done():
		t.Fatal("lock wait timed out")
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

func TestBalanceV2MigrationPreservesExistingBuildings(t *testing.T) {
	if os.Getenv("TEST_CONTAINERS") != "1" {
		t.Skip("set TEST_CONTAINERS=1 to start a PostgreSQL container")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: testcontainers.ContainerRequest{
			Image: "postgres:16-alpine", ExposedPorts: []string{"5432/tcp"},
			Env:        map[string]string{"POSTGRES_DB": "real_city", "POSTGRES_USER": "real_city", "POSTGRES_PASSWORD": "real_city"},
			WaitingFor: wait.ForListeningPort("5432/tcp").WithStartupTimeout(time.Minute),
		},
		Started: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = container.Terminate(context.Background()) })
	host, err := container.Host(ctx)
	if err != nil {
		t.Fatal(err)
	}
	port, err := container.MappedPort(ctx, "5432/tcp")
	if err != nil {
		t.Fatal(err)
	}
	dsn := fmt.Sprintf("postgres://real_city:real_city@%s:%s/real_city?sslmode=disable", host, port.Port())

	preV2Dir := t.TempDir()
	migrationSource := filepath.Clean("../../../db/migrations")
	files, err := os.ReadDir(migrationSource)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range files {
		if len(entry.Name()) < 6 || entry.IsDir() || filepath.Ext(entry.Name()) != ".sql" {
			continue
		}
		version, parseErr := strconv.ParseInt(entry.Name()[:6], 10, 64)
		if parseErr != nil || version > 37 {
			continue
		}
		data, err := os.ReadFile(filepath.Join(migrationSource, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(preV2Dir, entry.Name()), data, 0o600); err != nil {
			t.Fatal(err)
		}
	}
	runMigrations := func(directory string) {
		t.Helper()
		absoluteDirectory, err := filepath.Abs(directory)
		if err != nil {
			t.Fatal(err)
		}
		command := exec.CommandContext(ctx, "go", "run", "./cmd/migrate", "up")
		command.Dir = "../../.."
		env := make([]string, 0, len(os.Environ())+2)
		for _, value := range os.Environ() {
			if strings.HasPrefix(value, "POSTGRES_DSN=") || strings.HasPrefix(value, "MIGRATIONS_DIR=") {
				continue
			}
			env = append(env, value)
		}
		command.Env = append(env, "POSTGRES_DSN="+dsn, "MIGRATIONS_DIR="+absoluteDirectory)
		if output, err := command.CombinedOutput(); err != nil {
			t.Fatalf("migrate up: %v\n%s", err, output)
		}
	}
	runMigrations(preV2Dir)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err := db.ExecContext(ctx, `
		INSERT INTO players(id,email,name,password_hash) VALUES ('balance-player','balance@example.invalid','BalancePlayer','hash');
		INSERT INTO world_maps(id,name,seed,chunk_size,spawn_radius) VALUES ('balance-world','World',2,16,2);
		INSERT INTO buildings(id,map_id,owner_id,type,name,level,state,health,tile_x,tile_y,footprint_w,footprint_h,started_at)
		VALUES
		 ('v2-villa','balance-world','balance-player','villa','Вилла',4,'active',25,1,1,1,1,now()),
		 ('v2-apartment','balance-world','balance-player','apartment_house','Многоквартирный дом',4,'active',40,2,1,1,1,now()),
		 ('v2-destroyed','balance-world','balance-player','apartment_house','Многоквартирный дом',4,'ruined',0,3,1,1,1,now());
	`); err != nil {
		t.Fatal(err)
	}
	runMigrations(migrationSource)

	var version int
	if err := db.QueryRowContext(ctx, `SELECT version FROM game_balance_version WHERE singleton=true`).Scan(&version); err != nil || version != 2 {
		t.Fatalf("balance version=%d, err=%v", version, err)
	}
	var villaLevel, villaHealth, apartmentLevel, apartmentHealth, destroyedLevel, destroyedHealth int
	if err := db.QueryRowContext(ctx, `SELECT level,health FROM buildings WHERE id='v2-villa'`).Scan(&villaLevel, &villaHealth); err != nil {
		t.Fatal(err)
	}
	if err := db.QueryRowContext(ctx, `SELECT level,health FROM buildings WHERE id='v2-apartment'`).Scan(&apartmentLevel, &apartmentHealth); err != nil {
		t.Fatal(err)
	}
	if err := db.QueryRowContext(ctx, `SELECT level,health FROM buildings WHERE id='v2-destroyed'`).Scan(&destroyedLevel, &destroyedHealth); err != nil {
		t.Fatal(err)
	}
	if villaLevel != 4 || villaHealth != 3875 {
		t.Errorf("villa level/health=%d/%d, want 4/3875", villaLevel, villaHealth)
	}
	if apartmentLevel != 1 || apartmentHealth != 4000 {
		t.Errorf("apartment level/health=%d/%d, want 1/4000", apartmentLevel, apartmentHealth)
	}
	if destroyedLevel != 1 || destroyedHealth != 0 {
		t.Errorf("destroyed apartment level/health=%d/%d, want 1/0", destroyedLevel, destroyedHealth)
	}
	var retained int
	if err := db.QueryRowContext(ctx, `SELECT count(*) FROM buildings WHERE map_id='balance-world' AND owner_id='balance-player'`).Scan(&retained); err != nil || retained != 3 {
		t.Errorf("retained buildings=%d, err=%v; want 3", retained, err)
	}
}
