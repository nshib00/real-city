package service

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

type uniqueMonsterEventRepo struct {
	*memory.MonsterRepo
	eventIDs map[string]bool
}

func (r *uniqueMonsterEventRepo) AddEvent(ctx context.Context, event monster.Event) error {
	if r.eventIDs[event.ID] {
		return errors.New("duplicate monster event ID")
	}
	r.eventIDs[event.ID] = true
	return r.MonsterRepo.AddEvent(ctx, event)
}

func TestMultipleWeaponsFireAtSameMonsterInOneTick(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, 10, 24, 12, 0, 0, 0, time.UTC)
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	buildings := memory.NewBuildingRepo()
	monsters := &uniqueMonsterEventRepo{MonsterRepo: memory.NewMonsterRepo(), eventIDs: make(map[string]bool)}
	for _, id := range []building.ID{"a_weapon", "b_weapon"} {
		if err := buildings.Create(ctx, building.Building{ID: id, MapID: DefaultWorldID, OwnerID: "owner", Type: building.TypeDefenseBoltThrower,
			Level: 1, State: building.StateActive, Health: 180, Tile: world.Coord{X: 0, Y: 0}, CannonEnabled: true}); err != nil {
			t.Fatal(err)
		}
	}
	if err := monsters.Create(ctx, monster.Monster{ID: "target", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee,
		State: monster.StateIdle, Tile: world.Coord{X: 1, Y: 0}, Health: 100, MaxHealth: 100, UpdatedAt: now.Add(-time.Second)}); err != nil {
		t.Fatal(err)
	}
	svc := NewCannonService(buildings, monsters, memory.NewEconomyRepo(), nil, nil, NewMonsterService(monsters, log), nil, nil, log)
	fired, err := svc.Tick(ctx, now, 10)
	if err != nil || fired != 2 {
		t.Fatalf("simultaneous shots: fired=%d, err=%v", fired, err)
	}
	target, err := monsters.FindByID(ctx, "target")
	if err != nil || target.Health != 64 || len(monsters.eventIDs) != 2 {
		t.Fatalf("target=%+v, event IDs=%d, err=%v", target, len(monsters.eventIDs), err)
	}
}

func TestDefenseWeaponTargetsMonsterAcrossWrappedWorld(t *testing.T) {
	for _, tc := range []struct {
		name     string
		weaponX  int
		monsterX int
	}{
		{name: "world edge", weaponX: 159, monsterX: 0},
		{name: "negative spawn coordinate", weaponX: 145, monsterX: -16},
	} {
		t.Run(tc.name, func(t *testing.T) {
			ctx := context.Background()
			now := time.Date(2026, 10, 24, 12, 0, 0, 0, time.UTC)
			log := slog.New(slog.NewTextHandler(io.Discard, nil))
			buildings := memory.NewBuildingRepo()
			monsters := memory.NewMonsterRepo()
			if err := buildings.Create(ctx, building.Building{ID: "weapon", MapID: DefaultWorldID, OwnerID: "owner", Type: building.TypeDefenseBoltThrower,
				Level: 1, State: building.StateActive, Health: 180, Tile: world.Coord{X: tc.weaponX}, CannonEnabled: true}); err != nil {
				t.Fatal(err)
			}
			if err := monsters.Create(ctx, monster.Monster{ID: "target", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee,
				State: monster.StateIdle, Tile: world.Coord{X: tc.monsterX}, Health: 100, MaxHealth: 100, UpdatedAt: now.Add(-time.Second)}); err != nil {
				t.Fatal(err)
			}
			svc := NewCannonService(buildings, monsters, memory.NewEconomyRepo(), nil, nil, NewMonsterService(monsters, log), nil, nil, log)
			fired, err := svc.Tick(ctx, now, 10)
			if err != nil || fired != 1 {
				t.Fatalf("wrapped target: fired=%d, err=%v", fired, err)
			}
			target, err := monsters.FindByID(ctx, "target")
			if err != nil || target.Health != 82 {
				t.Fatalf("target=%+v, err=%v", target, err)
			}
		})
	}
}

func TestDefenseWeaponLineOfSightRespectsWrappedBlocker(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	if err := buildings.Create(ctx, building.Building{ID: "wall", MapID: DefaultWorldID, Type: building.TypeStoneWall,
		State: building.StateActive, Tile: world.Coord{X: 0}, Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
		t.Fatal(err)
	}
	svc := NewCannonService(buildings, memory.NewMonsterRepo(), nil, nil, nil, nil, nil, nil, slog.Default())
	clear, err := svc.lineOfSight(ctx, building.Building{MapID: DefaultWorldID, Tile: world.Coord{X: 159}}, world.Coord{X: 1})
	if err != nil || clear {
		t.Fatalf("wrapped wall must block shot: clear=%v, err=%v", clear, err)
	}
}

func TestCannonFiresAtNearestMonsterAndSpendsOneCharge(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, 10, 17, 12, 0, 0, 0, time.UTC)
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	buildings := memory.NewBuildingRepo()
	monsters := memory.NewMonsterRepo()
	economyRepo := memory.NewEconomyRepo()
	economyService := NewEconomyService(economyRepo, buildings, log)
	owner := player.ID("cannon-owner")
	if err := buildings.Create(ctx, building.Building{
		ID: "cannon", MapID: DefaultWorldID, OwnerID: string(owner), Type: building.TypeDefenseCannon,
		Level: 1, State: building.StateActive, Health: 260, Tile: world.Coord{X: 0, Y: 0},
		Footprint: building.Footprint{Width: 1, Height: 1}, CannonEnabled: true,
	}); err != nil {
		t.Fatal(err)
	}
	for _, item := range []monster.Monster{
		{ID: "near", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee, State: monster.StateIdle, Tile: world.Coord{X: 1, Y: 0}, Health: 100, MaxHealth: 100, UpdatedAt: now.Add(-time.Second)},
		{ID: "far", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee, State: monster.StateIdle, Tile: world.Coord{X: 2, Y: 0}, Health: 1, MaxHealth: 100, UpdatedAt: now.Add(-time.Second)},
	} {
		if err := monsters.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	inventory, err := economyRepo.GetInventory(ctx, owner, 10000)
	if err != nil {
		t.Fatal(err)
	}
	inventory.Items[economy.ResourceStone] = 2
	if err := economyRepo.SaveInventory(ctx, inventory); err != nil {
		t.Fatal(err)
	}
	service := NewCannonService(buildings, monsters, economyRepo, nil, nil, NewMonsterService(monsters, log), economyService, nil, log)
	for _, shotTime := range []time.Time{now, now.Add(time.Second)} {
		fired, err := service.Tick(ctx, shotTime, 10)
		if err != nil {
			t.Fatal(err)
		}
		if (shotTime == now && fired != 1) || (shotTime != now && fired != 0) {
			t.Fatalf("fired = %d at %s", fired, shotTime)
		}
	}
	near, _ := monsters.FindByID(ctx, "near")
	far, _ := monsters.FindByID(ctx, "far")
	if near.Health != 45 || far.Health != 1 {
		t.Fatalf("unexpected targets: near=%d far=%d", near.Health, far.Health)
	}
	remaining, _ := economyRepo.GetInventory(ctx, owner, 10000)
	if remaining.Items[economy.ResourceStone] != 1 {
		t.Fatalf("charges remaining = %d", remaining.Items[economy.ResourceStone])
	}
	cannon, _ := buildings.FindByID(ctx, "cannon")
	if cannon.CannonTargetID != "near" || cannon.CannonNextAttackAt == nil || !cannon.CannonNextAttackAt.Equal(now.Add(12*time.Second)) {
		t.Fatalf("unexpected cannon cooldown: %+v", cannon)
	}
	remaining.Items[economy.ResourceStone] = 0
	if err := economyRepo.SaveInventory(ctx, remaining); err != nil {
		t.Fatal(err)
	}
	fired, err := service.Tick(ctx, now.Add(12*time.Second), 10)
	if err != nil || fired != 0 {
		t.Fatalf("cannon fired without ammunition: fired=%d err=%v", fired, err)
	}
	near, _ = monsters.FindByID(ctx, "near")
	if near.Health != 45 {
		t.Fatalf("monster damaged without ammunition: %d", near.Health)
	}
}

func TestCannonPublishesShotBeforeExactMonsterDamage(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	bus := NewEventBus(4)
	events := bus.Subscribe(ctx)
	svc := &CannonService{events: bus}
	cannon := building.Building{ID: "c1", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeDefenseCannon,
		Level: 1, Tile: world.Coord{X: 2, Y: 3}}
	target := monster.Monster{ID: "m1", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee,
		State: monster.StateDead, Tile: world.Coord{X: 3, Y: 3}, Health: 0, UpdatedAt: time.Now()}
	svc.publishShot(ctx, cannon, target, monster.LootDrop{}, 12)
	<-events // Обновление состояния орудия.
	shot := <-events
	hit := <-events
	shotPayload, ok := shot.Payload.(CannonShotPayload)
	if !ok || shot.Type != EventCannonShot || shotPayload.Damage != 12 {
		t.Fatalf("shot event: %#v", shot)
	}
	hitPayload, ok := hit.Payload.(MonsterPayload)
	if !ok || hit.Type != EventMonsterDied || hitPayload.Damage != 12 || hitPayload.Source != "cannon" {
		t.Fatalf("hit event: %#v", hit)
	}
}

func TestCannonStopsBelowQuarterHealth(t *testing.T) {
	cannon := building.Building{Type: building.TypeDefenseCannon, Level: 1, State: building.StateDamaged, Health: 64, CannonEnabled: true}
	if cannonCanFire(cannon, time.Now()) {
		t.Fatal("cannon with less than 25% HP can fire")
	}
	cannon.Health = 65
	if !cannonCanFire(cannon, time.Now()) {
		t.Fatal("cannon with exactly 25% HP cannot fire")
	}
}

func TestDefenseWeaponsContinuePastIdleBatch(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, 10, 23, 12, 0, 0, 0, time.UTC)
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	buildings := memory.NewBuildingRepo()
	monsters := memory.NewMonsterRepo()
	for _, item := range []building.Building{
		{ID: "a_idle", MapID: DefaultWorldID, OwnerID: "owner", Type: building.TypeDefenseBoltThrower, Level: 1, State: building.StateActive, Health: 180, Tile: world.Coord{X: 100, Y: 100}, CannonEnabled: true},
		{ID: "b_ready", MapID: DefaultWorldID, OwnerID: "owner", Type: building.TypeDefenseBoltThrower, Level: 1, State: building.StateActive, Health: 180, Tile: world.Coord{X: 0, Y: 0}, CannonEnabled: true},
	} {
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	if err := monsters.Create(ctx, monster.Monster{ID: "target", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee, State: monster.StateIdle, Tile: world.Coord{X: 1, Y: 0}, Health: 100, MaxHealth: 100, UpdatedAt: now.Add(-time.Second)}); err != nil {
		t.Fatal(err)
	}
	svc := NewCannonService(buildings, monsters, memory.NewEconomyRepo(), nil, nil, NewMonsterService(monsters, log), nil, nil, log)
	for tick, want := range []int{0, 1} {
		fired, err := svc.Tick(ctx, now.Add(time.Duration(tick)*time.Second), 1)
		if err != nil || fired != want {
			t.Fatalf("tick %d: fired=%d, want=%d, err=%v", tick, fired, want, err)
		}
	}
	target, err := monsters.FindByID(ctx, "target")
	if err != nil || target.Health != 82 {
		t.Fatalf("monster health=%d, err=%v", target.Health, err)
	}
}

func TestOtherDefenseWeaponsUseTheirOwnStatsAndFuel(t *testing.T) {
	for _, tc := range []struct {
		kind           building.Type
		health, damage int
		cooldown       time.Duration
		fuel           int
	}{
		{building.TypeDefenseBoltThrower, 180, 18, 5 * time.Second, 0},
		{building.TypeDefenseStormCoil, 430, 90, 15 * time.Second, 1},
	} {
		t.Run(string(tc.kind), func(t *testing.T) {
			ctx := context.Background()
			now := time.Date(2026, 10, 19, 12, 0, 0, 0, time.UTC)
			log := slog.New(slog.NewTextHandler(io.Discard, nil))
			buildings := memory.NewBuildingRepo()
			monsters := memory.NewMonsterRepo()
			economyRepo := memory.NewEconomyRepo()
			owner := player.ID("defender")
			if err := buildings.Create(ctx, building.Building{ID: "weapon", MapID: DefaultWorldID, OwnerID: string(owner), Type: tc.kind,
				Level: 1, State: building.StateActive, Health: tc.health, Tile: world.Coord{X: 0, Y: 0}, CannonEnabled: true}); err != nil {
				t.Fatal(err)
			}
			if err := monsters.Create(ctx, monster.Monster{ID: "target", MapID: DefaultWorldID, Type: monster.TypeRoamingMelee,
				State: monster.StateIdle, Tile: world.Coord{X: 1, Y: 1}, Health: 180, MaxHealth: 180, UpdatedAt: now.Add(-time.Second)}); err != nil {
				t.Fatal(err)
			}
			if tc.fuel > 0 {
				inventory, err := economyRepo.GetInventory(ctx, owner, 10000)
				if err != nil {
					t.Fatal(err)
				}
				inventory.Items[economy.ResourceFuel] = tc.fuel
				if err := economyRepo.SaveInventory(ctx, inventory); err != nil {
					t.Fatal(err)
				}
			}
			service := NewCannonService(buildings, monsters, economyRepo, nil, nil, NewMonsterService(monsters, log), nil, nil, log)
			fired, err := service.Tick(ctx, now, 10)
			if err != nil || fired != 1 {
				t.Fatalf("fired=%d err=%v", fired, err)
			}
			got, _ := monsters.FindByID(ctx, "target")
			if got.Health != 180-tc.damage {
				t.Fatalf("health=%d", got.Health)
			}
			if tc.kind == building.TypeDefenseStormCoil && got.ShockUntil.Before(now.Add(2*time.Second)) {
				t.Fatalf("shock delay=%s", got.ShockUntil)
			}
			weapon, _ := buildings.FindByID(ctx, "weapon")
			if weapon.CannonNextAttackAt == nil || !weapon.CannonNextAttackAt.Equal(now.Add(tc.cooldown)) {
				t.Fatalf("cooldown=%v", weapon.CannonNextAttackAt)
			}
			if tc.kind == building.TypeDefenseStormCoil {
				inventory, _ := economyRepo.GetInventory(ctx, owner, 10000)
				if inventory.Items[economy.ResourceFuel] != 0 {
					t.Fatalf("fuel=%d", inventory.Items[economy.ResourceFuel])
				}
			}
		})
	}
}
