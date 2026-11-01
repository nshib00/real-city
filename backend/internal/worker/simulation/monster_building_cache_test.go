package simulation

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type countingBuildingRepo struct {
	*memory.BuildingRepo
	reads int
}

func (r *countingBuildingRepo) ListIntersectingFootprint(ctx context.Context, mapID string, minX, minY, maxX, maxY int) ([]building.Building, error) {
	r.reads++
	return r.BuildingRepo.ListIntersectingFootprint(ctx, mapID, minX, minY, maxX, maxY)
}

func TestTickBuildingCacheReusesNearbyReadsAndInvalidates(t *testing.T) {
	ctx := context.Background()
	repo := &countingBuildingRepo{BuildingRepo: memory.NewBuildingRepo()}
	item := building.Building{ID: "large", MapID: service.DefaultWorldID, Tile: world.Coord{X: 30, Y: 30}, Footprint: building.Footprint{Width: 4, Height: 4}}
	if err := repo.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	cache := newTickBuildingCache(repo)
	for _, rect := range [][4]int{{31, 31, 32, 32}, {32, 32, 33, 33}} {
		found, err := cache.listInRect(ctx, service.DefaultWorldID, rect[0], rect[1], rect[2], rect[3])
		if err != nil || len(found) != 1 || found[0].ID != item.ID {
			t.Fatalf("wrong footprint result: %+v, %v", found, err)
		}
	}
	if repo.reads != 4 {
		t.Fatalf("expected four shared spatial buckets, got %d reads", repo.reads)
	}
	cache.clear()
	if _, err := cache.listInRect(ctx, service.DefaultWorldID, 32, 32, 33, 33); err != nil {
		t.Fatal(err)
	}
	if repo.reads != 5 {
		t.Fatalf("expected fresh read after invalidation, got %d", repo.reads)
	}
	if err := repo.Delete(ctx, item.ID); err != nil {
		t.Fatal(err)
	}
	nextTick := newTickBuildingCache(repo)
	found, err := nextTick.listInRect(ctx, service.DefaultWorldID, 32, 32, 33, 33)
	if err != nil || len(found) != 0 {
		t.Fatalf("next tick reused removed building: %+v, %v", found, err)
	}
}

type countingMonsterEventRepo struct {
	*memory.MonsterRepo
	events int
}

func (r *countingMonsterEventRepo) AddEvent(ctx context.Context, event monster.Event) error {
	r.events++
	return r.MonsterRepo.AddEvent(ctx, event)
}

func TestMonsterMovementKeepsRealtimeWithoutHistoryInsert(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsters := &countingMonsterEventRepo{MonsterRepo: memory.NewMonsterRepo()}
	buildings := memory.NewBuildingRepo()
	item := monster.Monster{ID: "mover", MapID: service.DefaultWorldID, Type: monster.TypeRoamingMelee,
		State: monster.StateWandering, Tile: world.Coord{X: 1, Y: 1}, HomeTile: world.Coord{X: 1, Y: 1},
		Health: 100, MaxHealth: 100, SpeedTiles: 1, AggroRadius: 5, AttackRange: 1,
		UpdatedAt: now.Add(-time.Second)}
	if err := monsters.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if err := buildings.Create(ctx, building.Building{ID: "target", MapID: service.DefaultWorldID,
		Type: building.TypeDugout, State: building.StateActive, Health: 100, Tile: world.Coord{X: 3, Y: 1}}); err != nil {
		t.Fatal(err)
	}
	bus := service.NewEventBus(4)
	eventCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	received := bus.Subscribe(eventCtx)
	ai := NewMonsterAI(monsters, buildings, nil, bus, slog.Default())
	processed, err := ai.Tick(ctx, now, 1)
	if err != nil || processed != 1 {
		t.Fatalf("tick failed: %d, %v", processed, err)
	}
	if monsters.events != 0 {
		t.Fatalf("movement wrote %d history events", monsters.events)
	}
	select {
	case event := <-received:
		if event.Type != service.EventMonsterMoved {
			t.Fatalf("expected realtime movement, got %s", event.Type)
		}
	default:
		t.Fatal("movement was not published to realtime bus")
	}
}

type missingTargetRepo struct{ *memory.BuildingRepo }

func (r *missingTargetRepo) FindByID(context.Context, building.ID) (building.Building, error) {
	return building.Building{}, apperror.New(apperror.NotFound, "building removed")
}

func TestMonsterTickSkipsBuildingRemovedAfterTargetSelection(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsters := memory.NewMonsterRepo()
	buildings := &missingTargetRepo{BuildingRepo: memory.NewBuildingRepo()}
	item := monster.Monster{ID: "stale_target", MapID: service.DefaultWorldID, Type: monster.TypeRoamingMelee,
		State: monster.StateWandering, Tile: world.Coord{X: 10, Y: 10}, Health: 100, MaxHealth: 100,
		Damage: 10, AttackRange: 1, AggroRadius: 5, UpdatedAt: now.Add(-time.Second)}
	if err := monsters.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if err := buildings.Create(ctx, building.Building{ID: "removed", MapID: service.DefaultWorldID,
		Type: building.TypeDugout, State: building.StateActive, Tile: world.Coord{X: 11, Y: 10}, Health: 100}); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(monsters, buildings, nil, nil, slog.Default())
	processed, err := ai.Tick(ctx, now, 1)
	if err != nil || processed != 0 {
		t.Fatalf("stale target should be skipped: processed=%d err=%v", processed, err)
	}
}
