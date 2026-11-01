package main

import (
	"context"
	"io"
	"log/slog"
	"testing"

	"real-city/backend/pkg/config"
)

func TestConfiguredDatabaseFailureNeverStartsMemoryGame(t *testing.T) {
	cfg := config.Config{}
	cfg.Postgres.Driver = "invalid-driver"
	cfg.Postgres.DSN = "postgres://unavailable.invalid/real_city"
	application, err := newApp(cfg, slog.New(slog.NewTextHandler(io.Discard, nil)))
	if err == nil || application != nil {
		t.Fatal("database failure silently created an ephemeral game")
	}
	cfg.Postgres.DSN = ""
	cfg.AppEnv = "production"
	application, err = newApp(cfg, slog.New(slog.NewTextHandler(io.Discard, nil)))
	if err == nil || application != nil {
		t.Fatal("production without a persistent database was accepted")
	}
}

func TestStandaloneModeKeepsOutboxDispatcherInAPI(t *testing.T) {
	cfg := config.Config{Session: config.SessionConfig{Secret: "test-secret"}, Simulation: config.SimulationConfig{Embedded: false}}
	app, err := newApp(cfg, slog.New(slog.NewTextHandler(io.Discard, nil)))
	if err != nil {
		t.Fatal(err)
	}
	defer app.realtime.Shutdown()
	if app.sim != nil || app.outbox == nil {
		t.Fatal("standalone API must run outbox dispatcher without simulation")
	}
	if err := app.run(context.Background()); err == nil {
		t.Fatal("standalone API must reject an independent in-memory database")
	}
}
