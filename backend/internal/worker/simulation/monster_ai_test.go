package simulation

import (
	"context"
	"fmt"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

func TestMonsterAITickAggrosNearestBuilding(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsterRepo := memory.NewMonsterRepo()
	buildingRepo := memory.NewBuildingRepo()
	spec, _ := catalog.MonsterSpec(monster.TypeRoamingMelee)
	item := monster.Monster{
		ID: "test_monster", MapID: "dev-world", Type: spec.Type, State: monster.StateWandering,
		Tile: world.Coord{X: 1, Y: 1}, HomeTile: world.Coord{X: 1, Y: 1}, Health: spec.MaxHealth, MaxHealth: spec.MaxHealth,
		Damage: spec.Damage, SpeedTiles: spec.SpeedTiles, AggroRadius: spec.AggroRadius, AttackRange: spec.AttackRange,
		AttackCooldown: spec.AttackCooldown, LastMovedAt: now, CreatedAt: now, UpdatedAt: now,
	}
	if err := monsterRepo.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if err := buildingRepo.Create(ctx, building.Building{
		ID: "target", MapID: "dev-world", OwnerID: "p1", Type: building.TypeTownHall, State: building.StateActive,
		Tile: world.Coord{X: 3, Y: 1}, Health: 100, CreatedAt: now, UpdatedAt: now,
	}); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(monsterRepo, buildingRepo, nil, nil, slog.Default())
	processed, err := ai.Tick(ctx, now.Add(time.Second), 10)
	if err != nil {
		t.Fatal(err)
	}
	if processed == 0 {
		t.Fatal("expected processed monsters")
	}
	updated, err := monsterRepo.FindByID(ctx, item.ID)
	if err != nil {
		t.Fatal(err)
	}
	if updated.State != monster.StateAggro {
		t.Fatalf("expected aggro state, got %s", updated.State)
	}
	if updated.Tile != (world.Coord{X: 2, Y: 1}) {
		t.Fatalf("expected movement toward target, got %+v", updated.Tile)
	}
}

func TestWanderingMonsterWaitsForNextDecision(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC().Truncate(time.Second)
	monsters := memory.NewMonsterRepo()
	item := monster.Monster{ID: "scheduled_wanderer", MapID: "dev-world", Type: monster.TypeRoamingMelee,
		State: monster.StateWandering, Tile: world.Coord{X: 20, Y: 20}, HomeTile: world.Coord{X: 20, Y: 20},
		Health: 100, MaxHealth: 100, SpeedTiles: 1, UpdatedAt: now.Add(-time.Second)}
	if err := monsters.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(monsters, memory.NewBuildingRepo(), nil, nil, slog.Default())
	if _, err := ai.Tick(ctx, now, 10); err != nil {
		t.Fatal(err)
	}
	if due, err := monsters.ListActiveForTick(ctx, "dev-world", now.Add(time.Second), 10); err != nil {
		t.Fatal(err)
	} else {
		for _, candidate := range due {
			if candidate.ID == item.ID {
				t.Fatal("wandering monster was scheduled too early")
			}
		}
	}
	if due, err := monsters.ListActiveForTick(ctx, "dev-world", now.Add(2*time.Second), 10); err != nil {
		t.Fatal(err)
	} else {
		found := false
		for _, candidate := range due {
			found = found || candidate.ID == item.ID
		}
		if !found {
			t.Fatal("wandering monster was not scheduled again")
		}
	}
}

func TestNewBuildingWakesNearbyWanderingMonster(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC().Truncate(time.Second)
	monsters := memory.NewMonsterRepo()
	for _, item := range []monster.Monster{
		{ID: "near", MapID: service.DefaultWorldID, Type: monster.TypeRoamingMelee, State: monster.StateWandering,
			Tile: world.Coord{X: 159, Y: 4}, Health: 100, AggroRadius: 5, UpdatedAt: now},
		{ID: "far", MapID: service.DefaultWorldID, Type: monster.TypeRoamingMelee, State: monster.StateWandering,
			Tile: world.Coord{X: 80, Y: 80}, Health: 100, AggroRadius: 5, UpdatedAt: now},
	} {
		if err := monsters.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
		if applied, err := monsters.UpdateIfCurrent(ctx, item, item); err != nil || !applied {
			t.Fatalf("schedule %s: applied=%v err=%v", item.ID, applied, err)
		}
	}
	if err := monsters.WakeNearBuilding(ctx, service.DefaultWorldID, world.Coord{X: 1, Y: 4}, building.Footprint{Width: 1, Height: 1}, now.Add(time.Second)); err != nil {
		t.Fatal(err)
	}
	due, err := monsters.ListActiveForTick(ctx, service.DefaultWorldID, now.Add(time.Second), 100)
	if err != nil {
		t.Fatal(err)
	}
	found := map[monster.ID]bool{}
	for _, item := range due {
		found[item.ID] = true
	}
	if !found["near"] || found["far"] {
		t.Fatalf("wrong wake set: near=%v far=%v", found["near"], found["far"])
	}
}

func TestMonsterAIDamagesAndRuinsBuilding(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsters, buildings := memory.NewMonsterRepo(), memory.NewBuildingRepo()
	item := monster.Monster{ID: "attacker", MapID: "dev-world", Type: monster.TypeRoamingMelee,
		State: monster.StateWandering, Tile: world.Coord{X: 10, Y: 10}, Health: 100, MaxHealth: 100,
		Damage: 18, AttackRange: 1, AggroRadius: 5, AttackCooldown: time.Second,
		UpdatedAt: now.Add(-time.Hour)}
	if err := monsters.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if err := buildings.Create(ctx, building.Building{ID: "house", MapID: "dev-world", Type: building.TypeDugout,
		State: building.StateActive, Tile: world.Coord{X: 11, Y: 10}, Health: 30}); err != nil {
		t.Fatal(err)
	}
	events := service.NewEventBus(16)
	eventCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	received := events.Subscribe(eventCtx)
	ai := NewMonsterAI(monsters, buildings, nil, events, slog.Default())
	for _, tick := range []time.Time{now, now.Add(2 * time.Second)} {
		if _, err := ai.Tick(ctx, tick, 10); err != nil {
			t.Fatal(err)
		}
	}
	target, err := buildings.FindByID(ctx, "house")
	if err != nil || target.State != building.StateRuined || target.Health != 0 {
		t.Fatalf("building was not ruined: %+v err=%v", target, err)
	}
	monsterHits := 0
	for len(received) > 0 {
		event := <-received
		if event.Type == service.EventBuildingUpdated {
			payload := event.Payload.(service.BuildingPayload)
			if payload.Reason != "monster_attack" {
				t.Fatalf("expected monster attack reason, got %q", payload.Reason)
			}
			monsterHits++
			if payload.Damage != 18 && payload.Damage != 12 {
				t.Fatalf("wrong confirmed damage: %d", payload.Damage)
			}
		}
	}
	if monsterHits != 2 {
		t.Fatalf("expected two building hit events, got %d", monsterHits)
	}
}

func TestMonsterAIFallsBackToReachableWall(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsters, buildings := memory.NewMonsterRepo(), memory.NewBuildingRepo()
	attacker := monster.Monster{ID: "blocked_attacker", MapID: "dev-world", Type: monster.TypeRoamingMelee,
		State: monster.StateWandering, Tile: world.Coord{X: 10, Y: 10}, Health: 100, MaxHealth: 100,
		Damage: 18, SpeedTiles: 1, AttackRange: 1, AggroRadius: 5, AttackCooldown: time.Second}
	if err := monsters.Create(ctx, attacker); err != nil {
		t.Fatal(err)
	}
	for _, item := range []building.Building{
		{ID: "preferred", MapID: "dev-world", Type: building.TypeDugout, State: building.StateActive, Tile: world.Coord{X: 13, Y: 10}, Health: 100},
		{ID: "wall_left", MapID: "dev-world", Type: building.TypeStoneWall, State: building.StateActive, Tile: world.Coord{X: 12, Y: 10}, Health: 100},
		{ID: "wall_right", MapID: "dev-world", Type: building.TypeStoneWall, State: building.StateActive, Tile: world.Coord{X: 14, Y: 10}, Health: 100},
		{ID: "wall_top", MapID: "dev-world", Type: building.TypeStoneWall, State: building.StateActive, Tile: world.Coord{X: 13, Y: 9}, Health: 100},
		{ID: "wall_bottom", MapID: "dev-world", Type: building.TypeStoneWall, State: building.StateActive, Tile: world.Coord{X: 13, Y: 11}, Health: 100},
	} {
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	ai := NewMonsterAI(monsters, buildings, nil, nil, slog.Default())
	for _, tick := range []time.Time{now, now.Add(time.Second), now.Add(2 * time.Second)} {
		if _, err := ai.Tick(ctx, tick, 10); err != nil {
			t.Fatal(err)
		}
	}
	wall, err := buildings.FindByID(ctx, "wall_left")
	if err != nil || wall.Health >= 100 {
		t.Fatalf("reachable wall was not attacked: %+v, %v", wall, err)
	}
}

func TestMonsterAIDestroysCapturedRuinImmediately(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsters, buildings := memory.NewMonsterRepo(), memory.NewBuildingRepo()
	item := monster.Monster{ID: "ruin_attacker", MapID: "dev-world", Type: monster.TypeRoamingMelee,
		State: monster.StateWandering, Tile: world.Coord{X: 10, Y: 10}, Health: 100, MaxHealth: 100,
		Damage: 18, AttackRange: 1, AggroRadius: 5, AttackCooldown: time.Second,
		UpdatedAt: now.Add(-time.Hour)}
	if err := monsters.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	if err := buildings.Create(ctx, building.Building{ID: "captured_ruin", MapID: "dev-world", OwnerID: "p1", Type: "ruins_archive",
		State: building.StateActive, Tile: world.Coord{X: 11, Y: 10}, Health: 10}); err != nil {
		t.Fatal(err)
	}
	events := service.NewEventBus(16)
	eventCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	received := events.Subscribe(eventCtx)
	ai := NewMonsterAI(monsters, buildings, nil, events, slog.Default())
	if _, err := ai.Tick(ctx, now, 1); err != nil {
		t.Fatal(err)
	}
	if _, err := buildings.FindByID(ctx, "captured_ruin"); err == nil {
		t.Fatal("destroyed ruin still has an owner")
	}
	for len(received) > 0 {
		event := <-received
		if event.Type == service.EventBuildingRemoved {
			payload := event.Payload.(service.BuildingRemovedPayload)
			if payload.Reason != "monster_attack" {
				t.Fatalf("expected monster attack reason, got %q", payload.Reason)
			}
			return
		}
	}
	t.Fatal("missing monster attack removal event")
}

func TestMonsterPathAvoidsTerrainAndPlayerBuildings(t *testing.T) {
	ctx := context.Background()
	worlds, buildings := memory.NewWorldRepo(), memory.NewBuildingRepo()
	blocked := map[world.Coord]world.TerrainType{
		{X: 41, Y: 40}: world.TerrainForest,
		{X: 41, Y: 41}: world.TerrainWater,
		{X: 40, Y: 41}: world.TerrainMountain,
		{X: 42, Y: 40}: world.TerrainRuins,
		{X: 42, Y: 41}: world.TerrainOilWell,
	}
	for y := 36; y <= 44; y++ {
		for x := 36; x <= 47; x++ {
			coord := world.Coord{X: x, Y: y}
			chunk, _, err := worlds.GetOrCreateChunk(ctx, "dev-world", world.ChunkForTile(coord))
			if err != nil {
				t.Fatal(err)
			}
			for _, tile := range chunk.Tiles {
				if tile.Coord == coord {
					tile.Terrain = world.TerrainGrass
					if terrain, ok := blocked[coord]; ok {
						tile.Terrain = terrain
					}
					if err := worlds.UpdateTile(ctx, tile); err != nil {
						t.Fatal(err)
					}
				}
			}
		}
	}
	if err := buildings.Create(ctx, building.Building{ID: "wall", MapID: "dev-world", Type: building.TypeStoneWall,
		State: building.StateActive, Tile: world.Coord{X: 41, Y: 39}, Health: 100}); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, worlds, nil, slog.Default())
	path, err := ai.nextPassablePath(ctx, world.Coord{X: 40, Y: 40}, world.Coord{X: 43, Y: 40}, 20, 0, make(map[world.ChunkCoord]world.Chunk))
	if err != nil || len(path) == 0 {
		t.Fatalf("no path around obstacles: path=%v err=%v", path, err)
	}
	for _, tile := range path {
		if _, forbidden := blocked[tile]; forbidden || tile == (world.Coord{X: 41, Y: 39}) {
			t.Fatalf("path crossed forbidden tile: %v", path)
		}
		chunk, _, err := worlds.GetOrCreateChunk(ctx, "dev-world", world.ChunkForTile(tile))
		if err != nil {
			t.Fatal(err)
		}
		local := world.TileLocalCoord(tile)
		if chunk.Tiles[local.Y*world.ChunkSize+local.X].Terrain != world.TerrainGrass {
			t.Fatalf("path left grass terrain: %v", path)
		}
	}
}

func TestEmberWispFliesAcrossBuildingsExceptHighWalls(t *testing.T) {
	for _, tc := range []struct {
		kind      building.Type
		fliesOver bool
	}{
		{building.TypeStoneWall, true},
		{building.TypeLumberYard, true},
		{building.TypeConcreteWall, false},
		{building.TypeModernWall, false},
	} {
		t.Run(string(tc.kind), func(t *testing.T) {
			ctx := context.Background()
			buildings := memory.NewBuildingRepo()
			if err := buildings.Create(ctx, building.Building{ID: "obstacle", MapID: service.DefaultWorldID, Type: tc.kind,
				State: building.StateActive, Tile: world.Coord{X: 41, Y: 40}, Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
				t.Fatal(err)
			}
			ai := NewMonsterAI(nil, buildings, nil, nil, slog.Default())
			path, err := ai.nextPassablePathCached(ctx, world.Coord{X: 40, Y: 40}, world.Coord{X: 43, Y: 40}, 3, 0, true, make(map[world.ChunkCoord]world.Chunk), nil)
			if err != nil || len(path) == 0 {
				t.Fatalf("path=%v err=%v", path, err)
			}
			crosses := false
			for _, tile := range path {
				crosses = crosses || tile == (world.Coord{X: 41, Y: 40})
			}
			if crosses != tc.fliesOver {
				t.Fatalf("path=%v crosses obstacle=%v want=%v", path, crosses, tc.fliesOver)
			}
		})
	}
}

func TestMonsterAITargetPreferencesAndFallback(t *testing.T) {
	cases := []struct {
		name      string
		kind      monster.Type
		preferred building.Type
		fallback  building.Type
	}{
		{"налётчик", monster.TypeRoamingMelee, building.TypeDugout, building.TypeTownHall},
		{"страж залежи", monster.TypeResourceGuardian, building.TypeClayQuarry, building.TypeTownHall},
		{"сторож руин", monster.TypeRuinsGuardian, building.TypeCoinStorage, building.TypeTownHall},
		{"лесной следопыт", monster.TypeForestStalker, building.TypeLumberYard, building.TypeTownHall},
		{"споровый зверь", monster.TypeSporeBeast, building.TypeFieldBed, building.TypeTownHall},
		{"железоспин", monster.TypeIronbackBrute, building.TypeStoneWall, building.TypeTownHall},
		{"тлеющий огонёк", monster.TypeEmberWisp, building.TypeWorkshop, building.TypeTownHall},
		{"колосс", monster.TypeAncientColossus, building.TypeTownHall, building.TypeCoinStorage},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			ctx := context.Background()
			buildings := memory.NewBuildingRepo()
			for _, b := range []building.Building{
				{ID: "fallback", MapID: "dev-world", Type: tc.fallback, State: building.StateActive, Tile: world.Coord{X: 31}, Health: 100},
				{ID: "preferred", MapID: "dev-world", Type: tc.preferred, State: building.StateActive, Tile: world.Coord{X: 34}, Health: 100},
			} {
				if err := buildings.Create(ctx, b); err != nil {
					t.Fatal(err)
				}
			}
			ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, nil, nil, slog.Default())
			item := monster.Monster{MapID: "dev-world", Type: tc.kind, Tile: world.Coord{X: 30}, AggroRadius: 5}
			target, ok, err := ai.nearestTarget(ctx, item)
			if err != nil || !ok || target.ID != "preferred" {
				t.Fatalf("preferred target across chunk: target=%s ok=%v err=%v", target.ID, ok, err)
			}
			item.AggroRadius = 2
			target, ok, err = ai.nearestTarget(ctx, item)
			if err != nil || !ok || target.ID != "fallback" {
				t.Fatalf("fallback when preferred is outside aggro: target=%s ok=%v err=%v", target.ID, ok, err)
			}
		})
	}
}

func TestMonsterAITargetsNearestFootprintTileAndSkipsInvalidBuildings(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	for _, b := range []building.Building{
		{ID: "preferred", MapID: "dev-world", Type: building.TypeCoinStorage, State: building.StateActive,
			Tile: world.Coord{X: 34}, Footprint: building.Footprint{Width: 4, Height: 1}, Health: 100},
		{ID: "ruined", MapID: "dev-world", Type: building.TypeCoinStorage, State: building.StateRuined,
			Tile: world.Coord{X: 31}, Health: 0},
		{ID: "trap", MapID: "dev-world", Type: building.TypeDefenseStakes, State: building.StateActive,
			Tile: world.Coord{X: 31}, Health: 100},
	} {
		if err := buildings.Create(ctx, b); err != nil {
			t.Fatal(err)
		}
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, nil, nil, slog.Default())
	item := monster.Monster{MapID: "dev-world", Type: monster.TypeRuinsGuardian, Tile: world.Coord{X: 38}, AggroRadius: 1}
	target, ok, err := ai.nearestTarget(ctx, item)
	if err != nil || !ok || target.ID != "preferred" || closestBuildingTile(item.Tile, target) != (world.Coord{X: 37}) {
		t.Fatalf("footprint target: target=%+v ok=%v err=%v", target, ok, err)
	}
}

func TestMonsterAIAggrosBuildingAcrossWrappedEdge(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	if err := buildings.Create(ctx, building.Building{ID: "edge_target", MapID: "dev-world", Type: building.TypeDugout,
		State: building.StateActive, Tile: world.Coord{X: 0, Y: 10}, Health: 30}); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, nil, nil, slog.Default())
	item := monster.Monster{MapID: "dev-world", Type: monster.TypeRoamingMelee,
		Tile: world.Coord{X: 159, Y: 10}, AggroRadius: 5}
	target, found, err := ai.nearestTarget(ctx, item)
	if err != nil || !found || target.ID != "edge_target" || wrappedManhattan(item.Tile, target.Tile) != 1 {
		t.Fatalf("wrapped target: %+v found=%v err=%v", target, found, err)
	}
}

func TestMonsterAIFallbackFavorsWeaponsAndWalls(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	for _, item := range []building.Building{
		{ID: "ordinary", MapID: "dev-world", Type: building.TypeCoinStorage, State: building.StateActive, Tile: world.Coord{X: 1}, Health: 100},
		{ID: "weapon", MapID: "dev-world", Type: building.TypeDefenseCannon, State: building.StateActive, Tile: world.Coord{X: 3}, Health: 100},
	} {
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, nil, nil, slog.Default())
	chosen := 0
	for i := 0; i < 100; i++ {
		item := monster.Monster{ID: monster.ID(fmt.Sprintf("monster-%d", i)), MapID: "dev-world",
			Type: monster.TypeRoamingMelee, AggroRadius: 5}
		target, found, err := ai.nearestTarget(ctx, item)
		if err != nil || !found {
			t.Fatalf("fallback target: found=%v err=%v", found, err)
		}
		if target.ID == "weapon" {
			chosen++
		}
	}
	if chosen < 60 {
		t.Fatalf("weapon selected only %d/100 times", chosen)
	}
}

func TestMonsterAITargetSelectionIsDeterministicAndLimitedByAggroRadius(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	for _, b := range []building.Building{
		{ID: "z-house", MapID: "dev-world", Type: building.TypeDugout, State: building.StateActive,
			Tile: world.Coord{X: 1}, Health: 35},
		{ID: "a-house", MapID: "dev-world", Type: building.TypeDugout, State: building.StateActive,
			Tile: world.Coord{Y: 1}, Health: 35},
	} {
		if err := buildings.Create(ctx, b); err != nil {
			t.Fatal(err)
		}
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, nil, nil, slog.Default())
	item := monster.Monster{MapID: "dev-world", Type: monster.TypeRoamingMelee, AggroRadius: 1}
	target, ok, err := ai.nearestTarget(ctx, item)
	if err != nil || !ok || target.ID != "a-house" {
		t.Fatalf("equal-distance tie: target=%s ok=%v err=%v", target.ID, ok, err)
	}
	item.AggroRadius = 0
	_, ok, err = ai.nearestTarget(ctx, item)
	if err != nil || ok {
		t.Fatalf("target outside aggro radius: ok=%v err=%v", ok, err)
	}
}

func TestMonsterAIAvoidsOccupiedTrapTile(t *testing.T) {
	ctx := context.Background()
	now := time.Now().UTC()
	monsters := memory.NewMonsterRepo()
	buildings := memory.NewBuildingRepo()
	start := monster.Monster{ID: "fast", MapID: "dev-world", Type: monster.TypeForestStalker,
		State: monster.StateWandering, Tile: world.Coord{X: 0, Y: 0}, HomeTile: world.Coord{X: 0, Y: 0},
		Health: 150, MaxHealth: 150, SpeedTiles: 2, AggroRadius: 5, AttackRange: 1,
		AttackCooldown: 6 * time.Second, CreatedAt: now, UpdatedAt: now}
	if err := monsters.Create(ctx, start); err != nil {
		t.Fatal(err)
	}
	if err := buildings.Create(ctx, building.Building{ID: "trap", MapID: "dev-world", OwnerID: "owner",
		Type: building.TypeDefenseStakes, Level: 1, State: building.StateActive, Tile: world.Coord{X: 1, Y: 0},
		Health: 80, TrapCharges: 3, CreatedAt: now, UpdatedAt: now}); err != nil {
		t.Fatal(err)
	}
	if err := buildings.Create(ctx, building.Building{ID: "target", MapID: "dev-world", OwnerID: "owner",
		Type: building.TypeTownHall, State: building.StateActive, Tile: world.Coord{X: 4, Y: 0},
		Health: 100, CreatedAt: now, UpdatedAt: now}); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(monsters, buildings, nil, nil, slog.Default())
	if _, err := ai.Tick(ctx, now.Add(time.Second), 1); err != nil {
		t.Fatal(err)
	}
	got, err := monsters.FindByID(ctx, start.ID)
	if err != nil {
		t.Fatal(err)
	}
	trap, err := buildings.FindByID(ctx, "trap")
	if err != nil {
		t.Fatal(err)
	}
	if got.Tile == (world.Coord{X: 1, Y: 0}) || got.Health != 150 || trap.TrapCharges != 3 {
		t.Fatalf("monster entered an occupied tile: monster=%+v trap=%+v", got, trap)
	}
}

func TestDamagedTrapDoesNotTriggerBelowQuarterHealth(t *testing.T) {
	ctx := context.Background()
	buildings := memory.NewBuildingRepo()
	if err := buildings.Create(ctx, building.Building{ID: "trap", MapID: "dev-world", Type: building.TypeDefenseStakes,
		Level: 1, State: building.StateDamaged, Tile: world.Coord{X: 1, Y: 0}, Health: 19, TrapCharges: 3}); err != nil {
		t.Fatal(err)
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, nil, nil, slog.Default())
	item := monster.Monster{ID: "m", MapID: "dev-world", State: monster.StateIdle, Health: 100, MaxHealth: 100}
	if _, _, err := ai.applyTraps(ctx, &item, []world.Coord{{X: 1, Y: 0}}, time.Now().UTC()); err != nil {
		t.Fatal(err)
	}
	trap, err := buildings.FindByID(ctx, "trap")
	if err != nil {
		t.Fatal(err)
	}
	if item.Health != 100 || trap.TrapCharges != 3 {
		t.Fatalf("critical trap triggered: monster=%+v trap=%+v", item, trap)
	}
}

func TestResinSnareSlowsNextMovementWithoutStacking(t *testing.T) {
	ctx := context.Background()
	now := time.Date(2026, 10, 19, 12, 0, 0, 0, time.UTC)
	buildings := memory.NewBuildingRepo()
	for _, entry := range []building.Building{
		{ID: "a", MapID: "dev-world", Type: building.TypeDefenseResinSnare, Level: 1, State: building.StateActive, Tile: world.Coord{X: 1}, Health: 90, TrapCharges: 2},
		{ID: "b", MapID: "dev-world", Type: building.TypeDefenseResinSnare, Level: 1, State: building.StateActive, Tile: world.Coord{X: 2}, Health: 90, TrapCharges: 2},
	} {
		if err := buildings.Create(ctx, entry); err != nil {
			t.Fatal(err)
		}
	}
	ai := NewMonsterAI(memory.NewMonsterRepo(), buildings, nil, nil, slog.Default())
	ai.SetMoveInterval(2 * time.Second)
	item := monster.Monster{ID: "m", MapID: "dev-world", State: monster.StateIdle, Health: 100, MaxHealth: 100}
	if _, _, err := ai.applyTraps(ctx, &item, []world.Coord{{X: 1}, {X: 2}}, now); err != nil {
		t.Fatal(err)
	}
	if item.Health != 76 || !item.LastMovedAt.Equal(now.Add(3*time.Second)) {
		t.Fatalf("resin effect stacked or missed: %+v", item)
	}
}
