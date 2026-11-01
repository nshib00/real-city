package postgres

import (
	"context"
	"database/sql"
	"errors"
	"os"
	"strconv"
	"time"

	_ "github.com/lib/pq"
)

type DB struct {
	pool *sql.DB
}

func Open(ctx context.Context, driver string, dsn string) (*DB, error) {
	if dsn == "" {
		return nil, errors.New("postgres DSN is required")
	}
	pool, err := sql.Open(driver, dsn)
	if err != nil {
		return nil, err
	}
	maxOpen := poolSize("POSTGRES_MAX_OPEN_CONNS", 20)
	maxIdle := poolSize("POSTGRES_MAX_IDLE_CONNS", 10)
	if maxIdle > maxOpen {
		maxIdle = maxOpen
	}
	pool.SetMaxOpenConns(maxOpen)
	pool.SetMaxIdleConns(maxIdle)
	pool.SetConnMaxLifetime(30 * time.Minute)
	if err := pool.PingContext(ctx); err != nil {
		_ = pool.Close()
		return nil, err
	}
	return &DB{pool: pool}, nil
}

func poolSize(name string, fallback int) int {
	value, err := strconv.Atoi(os.Getenv(name))
	if err != nil || value < 1 || value > 100 {
		return fallback
	}
	return value
}

func (db *DB) Pool() *sql.DB {
	return db.pool
}

func (db *DB) Close() error {
	if db == nil || db.pool == nil {
		return nil
	}
	return db.pool.Close()
}
