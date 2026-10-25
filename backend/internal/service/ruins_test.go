package service

import (
	"context"
	"io"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/world"
)

func TestRuinRestorationTimesAndCosts(t *testing.T) {
	seen := map[time.Duration]bool{}
	for _, kind := range []building.Type{
		"ruins_town_square", "ruins_archive", "ruins_mint", "ruins_storage",
		"ruins_greenhouse", "ruins_water_station", "ruins_bastion", "ruins_mechanic_workshop",
		"ruins_wind_shrine", "ruins_ore_obelisk", "ruins_rift_watch", "ruins_river_lighthouse",
	} {
		spec, ok := catalog.GetBuilding(kind)
		if !ok || spec.BuildDuration < 20*time.Hour || spec.BuildDuration > 48*time.Hour || seen[spec.BuildDuration] || len(spec.Cost) == 0 || spec.Health <= 0 {
			t.Fatalf("invalid ruin restoration spec for %s: %+v", kind, spec)
		}
		seen[spec.BuildDuration] = true
	}
}

func TestRuinCaptureSaleAndDestructionReleaseOriginalTile(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	worlds := memory.NewWorldRepo()
	svc := NewBuildingService(repo, worlds, slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 10, 24, 12, 0, 0, 0, time.UTC)
	svc.SetNowForTest(func() time.Time { return now })
	coord := world.Coord{X: 40, Y: 40}
	chunk := world.ChunkForTile(coord)
	if _, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, chunk); err != nil {
		t.Fatal(err)
	}
	if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: coord, Chunk: chunk, Terrain: world.TerrainRuins, RuinType: "ruins_archive"}); err != nil {
		t.Fatal(err)
	}
	if _, err := svc.Place(ctx, PlaceBuildingInput{PlayerID: "p1", Type: "ruins_mint", Tile: coord}); err == nil {
		t.Fatal("wrong ruin type was accepted")
	}
	item, err := svc.Place(ctx, PlaceBuildingInput{PlayerID: "p1", Type: "ruins_archive", Tile: coord})
	if err != nil {
		t.Fatal(err)
	}
	if item.State != building.StateBuilding || item.CompletesAt == nil || item.CompletesAt.Sub(now) != 22*time.Hour || item.OwnerID != "p1" {
		t.Fatalf("ruin was not captured at restoration start: %+v", item)
	}
	if _, err := svc.Place(ctx, PlaceBuildingInput{PlayerID: "p2", Type: "ruins_archive", Tile: coord}); err == nil {
		t.Fatal("second player captured occupied ruin")
	}
	if _, err := svc.CompleteAt(ctx, item.ID, "p1", now.Add(21*time.Hour)); err == nil {
		t.Fatal("ruin completed before deadline")
	}
	completed, err := svc.CompleteAt(ctx, item.ID, "p1", now.Add(22*time.Hour))
	if err != nil || completed.State != building.StateActive || completed.Health <= 0 {
		t.Fatalf("ruin did not finish restoration: %+v %v", completed, err)
	}
	if err := svc.Demolish(ctx, item.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	verifyOriginalRuin(t, ctx, worlds, coord)
	now = now.Add(23 * time.Hour)
	second, err := svc.Place(ctx, PlaceBuildingInput{PlayerID: "p2", Type: "ruins_archive", Tile: coord})
	if err != nil {
		t.Fatal(err)
	}
	destroyed, applied, err := repo.DamageIfCurrent(ctx, second.ID, second.Health, second.Health, now)
	if err != nil || !applied || destroyed.State != building.StateRuined {
		t.Fatalf("ruin survived lethal damage: %+v %v", destroyed, err)
	}
	if err := svc.Demolish(ctx, second.ID, "p2"); err == nil {
		t.Fatal("destroyed ruin was sold")
	}
	if _, err := svc.CompleteDue(ctx, now, 100); err != nil {
		t.Fatal(err)
	}
	if _, err := repo.FindByID(ctx, second.ID); err == nil {
		t.Fatal("destroyed ruin still owned")
	}
	verifyOriginalRuin(t, ctx, worlds, coord)
	now = now.Add(time.Second)
	if _, err := svc.Place(ctx, PlaceBuildingInput{PlayerID: "p1", Type: "ruins_archive", Tile: coord}); err != nil {
		t.Fatalf("ruin cannot be recaptured after destruction: %v", err)
	}
}

func TestRuinRestorationCanBeRushedWithCrystals(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	worlds := memory.NewWorldRepo()
	svc := NewBuildingService(repo, worlds, slog.New(slog.NewTextHandler(io.Discard, nil)))
	now := time.Date(2026, 10, 24, 12, 0, 0, 0, time.UTC)
	svc.SetNowForTest(func() time.Time { return now })
	coord := world.Coord{X: 40, Y: 40}
	chunk := world.ChunkForTile(coord)
	if _, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, chunk); err != nil {
		t.Fatal(err)
	}
	if err := worlds.UpdateTile(ctx, world.Tile{MapID: DefaultWorldID, Coord: coord, Chunk: chunk, Terrain: world.TerrainRuins, RuinType: "ruins_archive"}); err != nil {
		t.Fatal(err)
	}
	item, err := svc.Place(ctx, PlaceBuildingInput{PlayerID: "p1", Type: "ruins_archive", Tile: coord})
	if err != nil {
		t.Fatal(err)
	}
	economyService := NewEconomyService(memory.NewEconomyRepo(), repo, slog.New(slog.NewTextHandler(io.Discard, nil)))
	svc.SetEconomy(economyService)
	cost := building.RushCompletionCrystalCost(item.CompletesAt.Sub(now))
	grantTestResources(t, ctx, economyService, "p1", economy.ResourceAmount{Resource: economy.ResourceAeolianCrystal, Amount: cost})
	if _, _, _, err := svc.RushComplete(ctx, item.ID, "p2"); err == nil {
		t.Fatal("another player rushed the ruin")
	}
	rushed, inventory, spent, err := svc.RushComplete(ctx, item.ID, "p1")
	if err != nil {
		t.Fatal(err)
	}
	if spent != cost || inventory.Items[economy.ResourceAeolianCrystal] != 0 {
		t.Fatalf("wrong crystal cost: spent=%d, expected=%d, inventory=%+v", spent, cost, inventory)
	}
	if rushed.State != building.StateActive || rushed.CompletesAt != nil {
		t.Fatalf("ruin restoration did not complete: %+v", rushed)
	}
	if _, err := svc.CompleteDue(ctx, now.Add(24*time.Hour), 100); err != nil {
		t.Fatal(err)
	}
	if _, _, spentAgain, err := svc.RushComplete(ctx, item.ID, "p1"); err != nil || spentAgain != 0 {
		t.Fatalf("completed ruin was charged again: cost=%d, err=%v", spentAgain, err)
	}
}

func verifyOriginalRuin(t *testing.T, ctx context.Context, worlds *memory.WorldRepo, coord world.Coord) {
	t.Helper()
	chunk, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(coord))
	if err != nil {
		t.Fatal(err)
	}
	tile, ok := findTile(chunk, coord)
	if !ok || tile.Terrain != world.TerrainRuins || tile.RuinType != "ruins_archive" {
		t.Fatalf("original ruin was changed: %+v", tile)
	}
}
