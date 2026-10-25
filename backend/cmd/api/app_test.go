package main

import (
	"context"
	"io"
	"log/slog"
	"testing"

	"real-city/backend/pkg/config"
)

func TestStandaloneModeKeepsOutboxDispatcherInAPI(t *testing.T) {
	cfg := config.Config{Session: config.SessionConfig{Secret: "test-secret"}, Simulation: config.SimulationConfig{Embedded: false}}
	app := newApp(cfg, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer app.realtime.Shutdown()
	if app.sim != nil || app.outbox == nil {
		t.Fatal("standalone API must run outbox dispatcher without simulation")
	}
	if err := app.run(context.Background()); err == nil {
		t.Fatal("standalone API must reject an independent in-memory database")
	}
}
