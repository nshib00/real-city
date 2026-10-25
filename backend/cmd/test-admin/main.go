package main

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	_ "github.com/lib/pq"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

// Keep below the historical INT maximum so normal game additions remain safe.
const testBalance = int64(2_000_000_000)
const testWeaponBalance = int64(1<<31 - 1)

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}

func run() error {
	if os.Getenv("APP_ENV") != "test" {
		return errors.New("test admin can only be created with APP_ENV=test")
	}
	email := player.NormalizeEmail(envOr("ADMIN_EMAIL", "admin@example.com"))
	name := strings.TrimSpace(envOr("ADMIN_NAME", "Test Admin"))
	password := envOr("ADMIN_PASSWORD", "admin12345")
	if err := player.ValidateEmail(email); err != nil {
		return err
	}
	if err := player.ValidateName(name); err != nil {
		return err
	}
	if err := player.ValidatePasswordPolicy(password); err != nil {
		return err
	}

	db, err := sql.Open("postgres", os.Getenv("POSTGRES_DSN"))
	if err != nil {
		return err
	}
	defer db.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		return fmt.Errorf("connect to test Postgres: %w", err)
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	var id, hash string
	err = tx.QueryRowContext(ctx, `SELECT id, password_hash FROM players WHERE email = $1 FOR UPDATE`, email).Scan(&id, &hash)
	switch {
	case errors.Is(err, sql.ErrNoRows):
		id, err = newPlayerID()
		if err != nil {
			return err
		}
		hash, err = player.HashPassword(password)
		if err != nil {
			return err
		}
		if _, err = tx.ExecContext(ctx, `INSERT INTO players (id, email, name, password_hash, role) VALUES ($1, $2, $3, $4, 'admin')`, id, email, name, hash); err != nil {
			return err
		}
		if _, err = tx.ExecContext(ctx, `INSERT INTO player_profiles (player_id, display_name, city_name) VALUES ($1, $2, $2)`, id, name); err != nil {
			return err
		}
	case err != nil:
		return err
	default:
		if err := player.ComparePassword(hash, password); err != nil {
			return fmt.Errorf("account %s exists with another password: %w", email, err)
		}
		if _, err = tx.ExecContext(ctx, `UPDATE players SET role = 'admin', updated_at = now() WHERE id = $1`, id); err != nil {
			return err
		}
	}

	resources := economy.AllResourceTypes()
	weaponCount := 0
	for _, resource := range resources {
		amount := testBalance
		if spec, ok := catalog.ResourceByType(resource); ok && spec.Category == "weapons" {
			amount = testWeaponBalance
			weaponCount++
		}
		if _, err := tx.ExecContext(ctx, `
			INSERT INTO player_inventories (player_id, resource, amount, updated_at)
			VALUES ($1, $2, $3, now())
			ON CONFLICT (player_id, resource)
			DO UPDATE SET amount = GREATEST(player_inventories.amount, EXCLUDED.amount), updated_at = now()
		`, id, resource, amount); err != nil {
			return fmt.Errorf("set %s balance: %w", resource, err)
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	fmt.Printf("Test admin ready: %s (%d resources at least %d each, including coins; %d weapons at least %d each)\n",
		email, len(resources), testBalance, weaponCount, testWeaponBalance)
	return nil
}

func envOr(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func newPlayerID() (string, error) {
	raw := make([]byte, 16)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	return "player_" + hex.EncodeToString(raw), nil
}
