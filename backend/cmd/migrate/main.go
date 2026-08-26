package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

const defaultDSN = "postgres://real_city:real_city@localhost:5432/real_city?sslmode=disable"

type migration struct {
	Version  int64
	FileName string
	Up       string
	Down     string
}

func main() {
	if len(os.Args) != 2 {
		log.Fatalf("usage: go run ./cmd/migrate [up|down|status]")
	}

	dsn := env("POSTGRES_DSN", defaultDSN)
	dir := env("MIGRATIONS_DIR", "db/migrations")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	if err := db.PingContext(ctx); err != nil {
		log.Fatal(err)
	}
	if err := ensureMigrationTable(ctx, db); err != nil {
		log.Fatal(err)
	}

	migrations, err := loadMigrations(dir)
	if err != nil {
		log.Fatal(err)
	}

	switch os.Args[1] {
	case "up":
		err = migrateUp(ctx, db, migrations)
	case "down":
		err = migrateDown(ctx, db, migrations)
	case "status":
		err = printStatus(ctx, db, migrations)
	default:
		err = fmt.Errorf("unknown command %q", os.Args[1])
	}
	if err != nil {
		log.Fatal(err)
	}
}

func ensureMigrationTable(ctx context.Context, db *sql.DB) error {
	_, err := db.ExecContext(ctx, `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version BIGINT PRIMARY KEY,
			filename TEXT NOT NULL,
			applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
		)
	`)
	return err
}

func migrateUp(ctx context.Context, db *sql.DB, migrations []migration) error {
	applied, err := appliedVersions(ctx, db)
	if err != nil {
		return err
	}
	for _, migration := range migrations {
		if applied[migration.Version] {
			continue
		}
		if err := applyMigration(ctx, db, migration, migration.Up, true); err != nil {
			return err
		}
		log.Printf("applied %s", migration.FileName)
	}
	return nil
}

func migrateDown(ctx context.Context, db *sql.DB, migrations []migration) error {
	applied, err := appliedVersions(ctx, db)
	if err != nil {
		return err
	}
	for i := len(migrations) - 1; i >= 0; i-- {
		migration := migrations[i]
		if !applied[migration.Version] {
			continue
		}
		if err := applyMigration(ctx, db, migration, migration.Down, false); err != nil {
			return err
		}
		log.Printf("rolled back %s", migration.FileName)
		return nil
	}
	log.Print("no applied migrations to roll back")
	return nil
}

func printStatus(ctx context.Context, db *sql.DB, migrations []migration) error {
	applied, err := appliedVersions(ctx, db)
	if err != nil {
		return err
	}
	for _, migration := range migrations {
		status := "pending"
		if applied[migration.Version] {
			status = "applied"
		}
		fmt.Printf("%06d %s %s\n", migration.Version, status, migration.FileName)
	}
	return nil
}

func applyMigration(ctx context.Context, db *sql.DB, migration migration, sqlBody string, up bool) (err error) {
	if strings.TrimSpace(sqlBody) == "" {
		return fmt.Errorf("%s has empty migration body", migration.FileName)
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer func() {
		if err != nil {
			_ = tx.Rollback()
		}
	}()

	if _, err = tx.ExecContext(ctx, sqlBody); err != nil {
		return fmt.Errorf("%s failed: %w", migration.FileName, err)
	}
	if up {
		_, err = tx.ExecContext(ctx, `
			INSERT INTO schema_migrations (version, filename)
			VALUES ($1, $2)
		`, migration.Version, migration.FileName)
	} else {
		_, err = tx.ExecContext(ctx, `
			DELETE FROM schema_migrations
			WHERE version = $1
		`, migration.Version)
	}
	if err != nil {
		return err
	}
	err = tx.Commit()
	return err
}

func appliedVersions(ctx context.Context, db *sql.DB) (map[int64]bool, error) {
	rows, err := db.QueryContext(ctx, `SELECT version FROM schema_migrations`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	applied := map[int64]bool{}
	for rows.Next() {
		var version int64
		if err := rows.Scan(&version); err != nil {
			return nil, err
		}
		applied[version] = true
	}
	return applied, rows.Err()
}

func loadMigrations(dir string) ([]migration, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	migrations := make([]migration, 0, len(entries))
	seen := map[int64]bool{}
	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".sql" {
			continue
		}
		version, err := parseVersion(entry.Name())
		if err != nil {
			return nil, err
		}
		if seen[version] {
			return nil, fmt.Errorf("duplicate migration version %d", version)
		}
		seen[version] = true

		body, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			return nil, err
		}
		up, down, err := splitMigration(string(body))
		if err != nil {
			return nil, fmt.Errorf("%s: %w", entry.Name(), err)
		}
		migrations = append(migrations, migration{Version: version, FileName: entry.Name(), Up: up, Down: down})
	}
	sort.Slice(migrations, func(i, j int) bool {
		return migrations[i].Version < migrations[j].Version
	})
	return migrations, nil
}

func parseVersion(name string) (int64, error) {
	prefix, _, ok := strings.Cut(name, "_")
	if !ok {
		prefix = strings.TrimSuffix(name, filepath.Ext(name))
	}
	version, err := strconv.ParseInt(prefix, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("invalid migration filename %q", name)
	}
	return version, nil
}

func splitMigration(body string) (string, string, error) {
	var up, down []string
	section := ""
	for _, line := range strings.Split(body, "\n") {
		switch strings.TrimSpace(line) {
		case "-- +goose Up":
			section = "up"
			continue
		case "-- +goose Down":
			section = "down"
			continue
		}
		switch section {
		case "up":
			up = append(up, line)
		case "down":
			down = append(down, line)
		}
	}
	if section == "" {
		return strings.TrimSpace(body), "", nil
	}
	if len(up) == 0 {
		return "", "", errors.New("missing -- +goose Up section")
	}
	if len(down) == 0 {
		return "", "", errors.New("missing -- +goose Down section")
	}
	return strings.TrimSpace(strings.Join(up, "\n")), strings.TrimSpace(strings.Join(down, "\n")), nil
}

func env(key string, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}
