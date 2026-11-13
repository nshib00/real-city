package worker

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/adapter/ws"
	"real-city/backend/internal/domain/building"
	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

func TestOutboxDispatcherPublishesEvent(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewOutboxRepo()
	bus := service.NewEventBus(2)
	events := bus.Subscribe(ctx)
	now := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	item := outbox.NewOutboxEvent("evt1", string(service.EventTileChanged), "tile:1:2", []byte(`{"ok":true}`), now)
	item.ChunkID = "dev-world:0:0"
	item.PlayerID = "p1"
	if err := repo.Append(ctx, item); err != nil {
		t.Fatalf("append outbox: %v", err)
	}

	dispatcher := NewOutboxDispatcher(repo, bus, slog.New(slog.NewTextHandler(io.Discard, nil)), config.SimulationConfig{BatchSize: 10, TickInterval: time.Second, LockTTL: time.Second})
	if dispatcher.cfg.OutboxDispatchInterval != 500*time.Millisecond || dispatcher.cfg.TickInterval != time.Second {
		t.Fatalf("simulation and outbox intervals are coupled: %+v", dispatcher.cfg)
	}
	dispatcher.now = func() time.Time { return now }
	if _, err := dispatcher.Dispatch(ctx); err != nil {
		t.Fatalf("dispatch: %v", err)
	}

	select {
	case event := <-events:
		if event.Type != service.EventTileChanged || event.ChunkID != "dev-world:0:0" {
			t.Fatalf("unexpected event: %#v", event)
		}
	case <-time.After(time.Second):
		t.Fatal("expected event")
	}
}

func TestOutboxDispatcherCompletesRevokedSharedEventWithoutPublishing(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewOutboxRepo()
	bus := service.NewEventBus(2)
	stream := bus.Subscribe(ctx)
	now := time.Date(2026, 11, 5, 12, 0, 0, 0, time.UTC)
	item := outbox.NewOutboxEvent("tower-share:incident:ally", string(service.EventTowerThreatShared), "incident", []byte(`{"incident_id":"incident","monster_type":"forest_stalker","region_x":4,"region_y":0,"detected_at":"2026-11-05T12:00:00Z"}`), now)
	item.PlayerID = "ally"
	if err := repo.Append(ctx, item); err != nil { t.Fatal(err) }
	dispatcher := NewOutboxDispatcher(repo, bus, slog.New(slog.NewTextHandler(io.Discard, nil)), config.SimulationConfig{BatchSize: 10, LockTTL: time.Second})
	dispatcher.now = func() time.Time { return now }
	checks := 0
	dispatcher.SetSharedTowerGuard(func(_ context.Context, _ string, _ func() error) (bool,error) { checks++; return false,nil })
	if count,err:=dispatcher.Dispatch(ctx); err!=nil || count!=1 { t.Fatalf("first dispatch count=%d err=%v",count,err) }
	if count,err:=dispatcher.Dispatch(ctx); err!=nil || count!=0 || checks!=1 { t.Fatalf("revoked event retried count=%d checks=%d err=%v",count,checks,err) }
	select { case event:=<-stream: t.Fatalf("revoked event leaked: %+v",event); default: }
}

func TestStandaloneWorkerEventReachesAPIBusWithClientPayload(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewOutboxRepo()
	workerBus := service.NewEventBus(2)
	workerBus.SetForwarder(service.NewOutboxForwarder(repo))
	apiBus := service.NewEventBus(2)
	apiEvents := apiBus.Subscribe(ctx)
	now := time.Now().UTC()
	buildingEvent := service.Event{
		Type: service.EventBuildingUpdated, ChunkID: "dev-world:0:0", PlayerID: "p1", CreatedAt: now,
		Payload: service.BuildingPayload{Building: building.Building{ID: "b1"}, Reason: "completed"},
	}
	if err := workerBus.Publish(buildingEvent); err != nil {
		t.Fatalf("worker publish: %v", err)
	}
	monsterEvent := service.Event{
		Type: service.EventMonsterMoved, ChunkID: "dev-world:0:0", CreatedAt: now,
		Payload: service.MonsterPayload{Monster: monster.Monster{ID: "m1", Type: monster.TypeForestStalker}},
	}
	if err := workerBus.Publish(monsterEvent); err != nil {
		t.Fatalf("worker publish monster: %v", err)
	}
	dispatcher := NewOutboxDispatcher(repo, apiBus, slog.New(slog.NewTextHandler(io.Discard, nil)), config.SimulationConfig{BatchSize: 10, LockTTL: time.Second})
	dispatcher.now = func() time.Time { return now }
	if count, err := dispatcher.Dispatch(ctx); err != nil || count != 2 {
		t.Fatalf("API dispatch: count=%d err=%v", count, err)
	}
	seen := map[service.EventType]bool{}
	for range 2 {
		select {
		case event := <-apiEvents:
			seen[event.Type] = true
			payload, ok := ws.EventEnvelope(event, 1).Payload.(map[string]any)
			if !ok {
				t.Fatalf("unexpected payload %T", event.Payload)
			}
			switch event.Type {
			case service.EventBuildingUpdated:
				converted, ok := payload["building"].(dto.BuildingResponse)
				if !ok || converted.ID != "b1" || event.PlayerID != "p1" || payload["reason"] != "completed" {
					t.Fatalf("building metadata lost: %#v", event)
				}
			case service.EventMonsterMoved:
				converted, ok := payload["monster"].(dto.MonsterResponse)
				if !ok || converted.ID != "m1" {
					t.Fatalf("monster public payload missing: %#v", payload)
				}
			}
		case <-time.After(time.Second):
			t.Fatal("event did not reach API bus")
		}
	}
	if !seen[service.EventBuildingUpdated] || !seen[service.EventMonsterMoved] {
		t.Fatalf("missing events: %#v", seen)
	}
}

func TestStandaloneTowerThreatRetainsPrivatePayload(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	repo := memory.NewOutboxRepo()
	workerBus := service.NewEventBus(2)
	workerBus.SetForwarder(service.NewOutboxForwarder(repo))
	apiBus := service.NewEventBus(2)
	stream := apiBus.Subscribe(ctx)
	now := time.Now().UTC()
	want := service.TowerThreatPayload{TowerID: "tower", MonsterID: "monster", MonsterType: "forest_stalker", TileX: 7, TileY: 9, TargetBuildingID: "home", DetectedAt: now}
	if err := workerBus.Publish(service.Event{Type: service.EventTowerThreatDetected, PlayerID: "owner", CreatedAt: now, Payload: want}); err != nil {
		t.Fatal(err)
	}
	dispatcher := NewOutboxDispatcher(repo, apiBus, slog.New(slog.NewTextHandler(io.Discard, nil)), config.SimulationConfig{BatchSize: 10, LockTTL: time.Second})
	dispatcher.now = func() time.Time { return now }
	if count, err := dispatcher.Dispatch(ctx); count != 1 || err != nil {
		t.Fatalf("dispatch=%d err=%v", count, err)
	}
	got := <-stream
	if got.PlayerID != "owner" || got.ChunkID != "" || got.Alliance != "" || got.Payload != want {
		t.Fatalf("private alert changed in outbox: %#v", got)
	}
}
