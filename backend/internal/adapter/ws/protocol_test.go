package ws

import (
	"testing"
	"time"

	"real-city/backend/internal/service"
)

func TestEventEnvelopeIncludesProtocolFields(t *testing.T) {
	event := service.Event{
		Type:      service.EventBuildingPlaced,
		ChunkID:   "dev-world:0:0",
		CreatedAt: time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC),
		Payload:   map[string]string{"ok": "true"},
	}

	envelope := EventEnvelope(event, 42)

	if envelope.Type != string(service.EventBuildingPlaced) {
		t.Fatalf("unexpected type %s", envelope.Type)
	}
	if envelope.Seq != 42 || envelope.ChunkID != "dev-world:0:0" || envelope.PayloadVersion != ProtocolVersion {
		t.Fatalf("unexpected envelope: %#v", envelope)
	}
	if envelope.EventID == "" || envelope.SentAt.IsZero() {
		t.Fatalf("expected event id and sent_at")
	}
}

func TestSubscriptionSetMatchesChannels(t *testing.T) {
	subs := NewSubscriptionSet()
	subs.SubscribeChunks([]string{"dev-world:1:2"})
	subs.SetPrivate(true)
	subs.SetAlliance("alliance:1")

	if !subs.Matches("dev-world:1:2", "", "", "player-1") {
		t.Fatal("expected chunk subscription match")
	}
	if !subs.Matches("", "player-1", "", "player-1") {
		t.Fatal("expected private subscription match")
	}
	if !subs.Matches("", "", "alliance:1", "player-1") {
		t.Fatal("expected alliance subscription match")
	}
	if subs.Matches("dev-world:9:9", "player-2", "alliance:2", "player-1") {
		t.Fatal("unexpected subscription match")
	}
}

func TestRateLimiterBlocksBurst(t *testing.T) {
	limiter := NewRateLimiter(2, time.Second)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)

	if !limiter.Allow(now) || !limiter.Allow(now) {
		t.Fatal("expected first two commands to pass")
	}
	if limiter.Allow(now) {
		t.Fatal("expected burst to be blocked")
	}
	if !limiter.Allow(now.Add(2 * time.Second)) {
		t.Fatal("expected next window to pass")
	}
}
