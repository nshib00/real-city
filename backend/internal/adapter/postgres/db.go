package postgres

import (
	"context"
	"database/sql"
	"errors"
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
	pool.SetMaxOpenConns(20)
	pool.SetMaxIdleConns(10)
	pool.SetConnMaxLifetime(30 * time.Minute)
	if err := pool.PingContext(ctx); err != nil {
		_ = pool.Close()
		return nil, err
	}
	return &DB{pool: pool}, nil
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
