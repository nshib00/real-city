package simulation

import (
	"context"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

func TestTowerDetectorPrivateThreatAndDeduplication(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	monsters := memory.NewMonsterRepo()
	bus := service.NewEventBus(10)
	stream := bus.Subscribe(ctx)
	now := time.Date(2026, 11, 5, 12, 0, 0, 0, time.UTC)
	target := building.Building{ID: "home", MapID: service.DefaultWorldID, OwnerID: "owner", Type: building.TypeTownHall, State: building.StateActive, Health: 100, Tile: world.Coord{X: 0, Y: 0}}
	for _, item := range []building.Building{
		target,
		{ID: "tower1", MapID: service.DefaultWorldID, OwnerID: "owner", Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100, Tile: world.Coord{X: 159, Y: 0}},
		{ID: "tower2", MapID: service.DefaultWorldID, OwnerID: "owner", Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100, Tile: world.Coord{X: 158, Y: 0}},
	} {
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	threat := monster.Monster{ID: "threat", MapID: service.DefaultWorldID, Type: monster.TypeForestStalker, State: monster.StateAggro, Tile: world.Coord{X: 1, Y: 0}, TargetType: "building", TargetID: "home", Health: 10}
	if err := monsters.Create(ctx, threat); err != nil {
		t.Fatal(err)
	}
	detector := NewTowerDetector(buildings, monsters, bus)
	for tick := 0; tick < 2; tick++ {
		count, err := detector.Tick(ctx, now.Add(time.Duration(tick)*time.Second))
		if err != nil || count != 1-tick {
			t.Fatalf("tick %d: count=%d err=%v", tick, count, err)
		}
	}
	event := <-stream
	if event.Type != service.EventTowerThreatDetected || event.PlayerID != player.ID("owner") || event.ChunkID != "" || event.Alliance != "" {
		t.Fatalf("alert leaked beyond private owner channel: %#v", event)
	}
	payload := event.Payload.(service.TowerThreatPayload)
	if payload.MonsterID != "threat" || payload.MonsterType != "forest_stalker" || payload.TileX != 1 || payload.TileY != 0 || payload.TargetBuildingID != "home" || !payload.DetectedAt.Equal(now) {
		t.Fatalf("unexpected alert payload: %#v", payload)
	}
	select {
	case extra := <-stream:
		t.Fatalf("duplicate alert: %#v", extra)
	default:
	}
	threat.Tile = world.Coord{X: 40, Y: 40}
	if err := monsters.Update(ctx, threat); err != nil {
		t.Fatal(err)
	}
	if count, err := detector.Tick(ctx, now.Add(towerScanInterval)); count != 0 || err != nil {
		t.Fatalf("outside: %d %v", count, err)
	}
	threat.Tile = world.Coord{X: 1, Y: 0}
	if err := monsters.Update(ctx, threat); err != nil {
		t.Fatal(err)
	}
	if count, err := detector.Tick(ctx, now.Add(2*towerScanInterval)); count != 0 || err != nil {
		t.Fatalf("cooldown: %d %v", count, err)
	}
	if count, err := detector.Tick(ctx, now.Add(towerAlertCooldown)); count != 0 || err != nil {
		t.Fatalf("stayed inside after cooldown: %d %v", count, err)
	}
	threat.Tile = world.Coord{X: 40, Y: 40}
	if err := monsters.Update(ctx, threat); err != nil {
		t.Fatal(err)
	}
	_, _ = detector.Tick(ctx, now.Add(towerAlertCooldown+towerScanInterval))
	threat.Tile = world.Coord{X: 1, Y: 0}
	if err := monsters.Update(ctx, threat); err != nil {
		t.Fatal(err)
	}
	if count, err := detector.Tick(ctx, now.Add(towerAlertCooldown+2*towerScanInterval)); count != 1 || err != nil {
		t.Fatalf("reentry: %d %v", count, err)
	}
}

func TestTowerDetectorLimitsRepositoryScans(t *testing.T) {
	ctx := context.Background()
	buildings := &countingTowerBuildings{BuildingRepository: memory.NewBuildingRepo()}
	monsters := &countingTowerMonsters{MonsterRepository: memory.NewMonsterRepo()}
	detector := NewTowerDetector(buildings, monsters, service.NewEventBus(2))
	now := time.Now().UTC()
	if err := buildings.Create(ctx, testTower(1, 100, world.Coord{})); err != nil {
		t.Fatal(err)
	}
	for i := range 100 {
		if _, err := detector.Tick(ctx, now.Add(time.Duration(i)*time.Millisecond)); err != nil {
			t.Fatal(err)
		}
	}
	if buildings.scans != 1 || monsters.scans != 1 {
		t.Fatalf("scans in 100 ms: buildings=%d monsters=%d", buildings.scans, monsters.scans)
	}
	if _, err := detector.Tick(ctx, now.Add(towerScanInterval)); err != nil {
		t.Fatal(err)
	}
	if buildings.scans != 2 || monsters.scans != 2 {
		t.Fatalf("next scheduled scan missing: buildings=%d monsters=%d", buildings.scans, monsters.scans)
	}
}

type countingTowerBuildings struct {
	service.BuildingRepository
	scans int
}

func (r *countingTowerBuildings) ListByMap(ctx context.Context, mapID string) ([]building.Building, error) {
	r.scans++
	return r.BuildingRepository.ListByMap(ctx, mapID)
}

type countingTowerMonsters struct {
	service.MonsterRepository
	scans int
}

func (r *countingTowerMonsters) ListByMap(ctx context.Context, mapID string) ([]monster.Monster, error) {
	r.scans++
	return r.MonsterRepository.ListByMap(ctx, mapID)
}

func TestTowerDetectorFiltersInactiveTowerAndIrrelevantMonsters(t *testing.T) {
	for _, test := range []struct {
		name    string
		tower   building.Building
		monster monster.Monster
		want    int
	}{
		{name: "level two boundary", tower: testTower(2, 150, world.Coord{}), monster: testThreat(world.Coord{X: 8, Y: 0}), want: 1},
		{name: "level two outside", tower: testTower(2, 150, world.Coord{}), monster: testThreat(world.Coord{X: 9, Y: 0})},
		{name: "level six boundary", tower: testTower(6, 520, world.Coord{}), monster: testThreat(world.Coord{X: 16, Y: 0}), want: 1},
		{name: "level six quarter health", tower: testTower(6, 130, world.Coord{}), monster: testThreat(world.Coord{X: 1, Y: 0})},
		{name: "upgrading", tower: func() building.Building {
			b := testTower(1, 100, world.Coord{})
			b.State = building.StateBuilding
			return b
		}(), monster: testThreat(world.Coord{X: 1, Y: 0})},
		{name: "wandering", tower: testTower(1, 100, world.Coord{}), monster: func() monster.Monster {
			m := testThreat(world.Coord{X: 1, Y: 0})
			m.State = monster.StateWandering
			return m
		}()},
		{name: "monster target", tower: testTower(1, 100, world.Coord{}), monster: func() monster.Monster { m := testThreat(world.Coord{X: 1, Y: 0}); m.TargetType = "monster"; return m }()},
		{name: "own summon", tower: testTower(1, 100, world.Coord{}), monster: func() monster.Monster { m := testThreat(world.Coord{X: 1, Y: 0}); m.CreatorID = "owner"; return m }()},
	} {
		t.Run(test.name, func(t *testing.T) {
			ctx := context.Background()
			buildings, monsters := memory.NewBuildingRepo(), memory.NewMonsterRepo()
			for _, b := range []building.Building{{ID: "home", MapID: service.DefaultWorldID, OwnerID: "owner", Type: building.TypeTownHall, State: building.StateActive, Health: 100}, test.tower} {
				if err := buildings.Create(ctx, b); err != nil {
					t.Fatal(err)
				}
			}
			if err := monsters.Create(ctx, test.monster); err != nil {
				t.Fatal(err)
			}
			count, err := NewTowerDetector(buildings, monsters, service.NewEventBus(2)).Tick(ctx, time.Now())
			if err != nil || count != test.want {
				t.Fatalf("alerts=%d, err=%v, want=%d", count, err, test.want)
			}
		})
	}
}

func testTower(level, health int, tile world.Coord) building.Building {
	return building.Building{ID: "tower", MapID: service.DefaultWorldID, OwnerID: "owner", Type: building.TypeTower, Level: level, State: building.StateActive, Health: health, Tile: tile}
}

func testThreat(tile world.Coord) monster.Monster {
	return monster.Monster{ID: "threat", MapID: service.DefaultWorldID, Type: monster.TypeRoamingMelee, State: monster.StateAggro, Tile: tile, TargetType: "building", TargetID: "home", Health: 10}
}
