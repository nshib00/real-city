package config

import (
	"testing"
	"time"
)

func TestLoadUsesFallbacks(t *testing.T) {
	t.Setenv("SERVER_ADDR", "")
	t.Setenv("SIMULATION_BATCH_SIZE", "bad")

	cfg := Load()

	if cfg.Server.Addr != ":8080" {
		t.Fatalf("expected default server addr, got %q", cfg.Server.Addr)
	}
	if cfg.Simulation.BatchSize != 100 {
		t.Fatalf("expected default batch size, got %d", cfg.Simulation.BatchSize)
	}
	if cfg.Session.AccessTTL != 15*time.Minute {
		t.Fatalf("expected default access ttl, got %s", cfg.Session.AccessTTL)
	}
	if cfg.Simulation.OutboxDispatchInterval != 500*time.Millisecond {
		t.Fatalf("expected independent outbox interval, got %s", cfg.Simulation.OutboxDispatchInterval)
	}
}
