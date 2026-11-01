package config

import (
	"reflect"
	"testing"
	"time"
)

func TestProductionSessionAndOriginsFromEnvironment(t *testing.T) {
	t.Setenv("CORS_ALLOWED_ORIGINS", "https://one.example, https://two.example")
	t.Setenv("JWT_ACCESS_TTL", "20m")
	t.Setenv("JWT_REFRESH_TTL", "168h")
	cfg := Load()
	if !reflect.DeepEqual(cfg.Server.AllowedOrigins, []string{"https://one.example", "https://two.example"}) {
		t.Fatalf("origins = %q", cfg.Server.AllowedOrigins)
	}
	if cfg.Session.AccessTTL != 20*time.Minute || cfg.Session.RefreshTTL != 7*24*time.Hour {
		t.Fatalf("session TTLs = %s / %s", cfg.Session.AccessTTL, cfg.Session.RefreshTTL)
	}
}

func TestProductionDoesNotDefaultToWildcardOrigin(t *testing.T) {
	t.Setenv("APP_ENV", "production")
	t.Setenv("CORS_ALLOWED_ORIGINS", "")
	if got := Load().Server.AllowedOrigins; len(got) != 0 {
		t.Fatalf("production origins = %q", got)
	}
}
