package ws

import (
	"testing"
	"time"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
)

func TestCombatPayloadUsesClientCoordinates(t *testing.T) {
	item := monster.Monster{ID: "m1", Type: monster.TypeForestStalker, State: monster.StateAggro, Health: 10}
	payload := EventEnvelope(service.Event{Type: service.EventMonsterMoved, Payload: service.MonsterPayload{Monster: item}}, 1).Payload.(map[string]any)
	converted, ok := payload["monster"].(dto.MonsterResponse)
	if !ok || converted.ID != "m1" || converted.Type != "forest_stalker" {
		t.Fatalf("monster payload not normalized: %#v", payload["monster"])
	}
	shot := EventEnvelope(service.Event{Type: service.EventCannonShot, Payload: service.CannonShotPayload{BuildingID: "b1", TileX: 4, TileY: 5}}, 2).Payload.(service.CannonShotPayload)
	if shot.TileX != 4 || shot.TileY != 5 {
		t.Fatalf("shot coordinates missing: %#v", shot)
	}
}

func TestPresenceMovementPayloadUsesClientCoordinates(t *testing.T) {
	payload := EventEnvelope(service.Event{Type: service.EventPresenceMoved, ChunkID: "dev-world:1:0", Payload: service.PresenceMovedPayload{
		Player: player.Presence{PlayerID: "p2", Name: "Аэрон", Level: 4, TileX: 33, TileY: 2},
	}}, 1).Payload.(map[string]any)
	item, ok := payload["player"].(player.Presence)
	if !ok || item.PlayerID != "p2" || item.Name != "Аэрон" || item.Level != 4 || item.TileX != 33 || item.TileY != 2 {
		t.Fatalf("movement payload not normalized: %#v", payload)
	}
}

func TestMonsterHitPayloadIncludesActualDamage(t *testing.T) {
	item := monster.Monster{ID: "m1", Type: monster.TypeRoamingMelee, Health: 0}
	payload := EventEnvelope(service.Event{Type: service.EventMonsterDied, Payload: service.MonsterPayload{
		Monster: item, Damage: 12, Source: "cannon",
	}}, 1).Payload.(map[string]any)
	if payload["damage"] != 12 || payload["source"] != "cannon" {
		t.Fatalf("monster damage missing: %#v", payload)
	}
}

func TestBuildingEventPreservesReason(t *testing.T) {
	payload := EventEnvelope(service.Event{Type: service.EventBuildingUpdated, Payload: service.BuildingPayload{
		Building: building.Building{ID: "b1"}, Reason: "monster_attack", Damage: 18,
	}}, 1).Payload.(map[string]any)
	if payload["reason"] != "monster_attack" || payload["damage"] != 18 {
		t.Fatalf("building hit lost: %#v", payload)
	}
	removed := EventEnvelope(service.Event{Type: service.EventBuildingRemoved, Payload: service.BuildingRemovedPayload{
		BuildingID: "ruin", Reason: "monster_attack", Damage: 10, TileX: 7, TileY: 8, BuildingType: "ruins_archive",
	}}, 2).Payload.(map[string]any)
	if removed["damage"] != 10 || removed["tile_x"] != 7 || removed["tile_y"] != 8 || removed["building_type"] != building.Type("ruins_archive") {
		t.Fatalf("removed building hit lost: %#v", removed)
	}
}

func TestTileEventPreservesForestReason(t *testing.T) {
	payload := EventEnvelope(service.Event{Type: service.EventTileChanged, Payload: service.TileChangedPayload{
		Reason: "forest_cut",
	}}, 1).Payload.(map[string]any)
	if payload["reason"] != "forest_cut" {
		t.Fatalf("forest reason lost: %#v", payload)
	}
}

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
