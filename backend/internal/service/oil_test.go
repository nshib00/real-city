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
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service/worldgen"
)

func TestOilExtractionLevels(t *testing.T) {
	for _, tc := range []struct {
		level             int
		interval          time.Duration
		output, depletion int
		workers           int
	}{
		{1, 30 * time.Minute, 100, 100, 15},
		{2, 25 * time.Minute, 250, 225, 21},
		{3, time.Hour, 400, 320, 27},
	} {
		interval, output, depletion := oilExtractionForLevel(tc.level)
		recipe := catalog.OilExtractionRecipe(tc.level)
		if interval != tc.interval || output != tc.output || depletion != tc.depletion || recipe.Workers != tc.workers {
			t.Fatalf("level %d: interval=%s output=%d depletion=%d", tc.level, interval, output, depletion)
		}
		if tc.level == 2 && (len(recipe.RareOutput) != 1 || recipe.RareOutput[0].Resource != economy.ResourceAmberEssence || recipe.RareOutput[0].Chance != 0.01) {
			t.Fatalf("level 2 rare output: %+v", recipe.RareOutput)
		}
		if tc.level == 3 && (len(recipe.RareOutput) != 2 || recipe.RareOutput[0].Chance != 0.02 || recipe.RareOutput[1].Resource != economy.ResourceQuietPowder || recipe.RareOutput[1].Chance != 0.005) {
			t.Fatalf("level 3 rare output: %+v", recipe.RareOutput)
		}
	}
}

func TestUpgradedOilWellProducesMoreOilAndPreservesDeposit(t *testing.T) {
	ctx := context.Background()
	players, xp := newExperienceTestPlayer(t)
	service, resources, buildings, nodes, _, well := oilFixture(t)
	if _, err := service.CompleteAt(ctx, well.ID, "p1", well.StartedAt.Add(11*time.Minute)); err != nil {
		t.Fatal(err)
	}
	well, err := buildings.FindByID(ctx, well.ID)
	if err != nil {
		t.Fatal(err)
	}
	well.Level = 2
	if err := buildings.Update(ctx, well); err != nil {
		t.Fatal(err)
	}
	node, err := nodes.FindResourceNode(ctx, "node_oil_1")
	if err != nil {
		t.Fatal(err)
	}
	production := NewProductionService(nodes, resources.economy, resources.log)
	production.SetBuildings(buildings)
	production.SetResources(resources)
	production.SetExperience(xp)
	production.randFloat = func() float64 { return 0 }
	production.now = func() time.Time { return node.UpdatedAt }
	grantTestResources(t, ctx, resources.economy, "p1", economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 21})
	job, _, err := production.Start(ctx, "p1", string(well.ID), "oil_extraction")
	if err != nil {
		t.Fatal(err)
	}
	if _, _, err := production.CompleteAt(ctx, "p1", job.ID, job.CompletesAt); err != nil {
		t.Fatal(err)
	}
	updated, err := nodes.FindResourceNode(ctx, node.ID)
	if err != nil {
		t.Fatal(err)
	}
	if updated.Amount != node.Amount-225 {
		t.Fatalf("oil deposit remaining = %d", updated.Amount)
	}
	inventory, err := nodes.GetInventory(ctx, "p1", 0)
	if err != nil {
		t.Fatal(err)
	}
	if inventory.Items[economy.ResourceOil] != 250 {
		t.Fatalf("oil output = %d", inventory.Items[economy.ResourceOil])
	}
	if inventory.Items[economy.ResourceAmberEssence] != 1 {
		t.Fatalf("rare amber essence = %d", inventory.Items[economy.ResourceAmberEssence])
	}
	if got, want := playerXP(t, players), catalog.ExperienceForBuilding(building.TypeOilWell, 2).Work; got != want {
		t.Fatalf("oil XP %d, want %d", got, want)
	}
}

func TestOilExtractionRequiresWorkersAndFullDepositCycle(t *testing.T) {
	ctx := context.Background()
	service, resources, buildings, nodes, _, well := oilFixture(t)
	if _, err := service.CompleteAt(ctx, well.ID, "p1", well.StartedAt.Add(11*time.Minute)); err != nil {
		t.Fatal(err)
	}
	production := NewProductionService(nodes, resources.economy, resources.log)
	production.SetBuildings(buildings)
	production.SetResources(resources)
	if _, _, err := production.Start(ctx, "p1", string(well.ID), catalog.OilExtractionRecipeID); err == nil {
		t.Fatal("oil extraction started without workers")
	}
	grantTestResources(t, ctx, resources.economy, "p1", economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 15})
	node, err := nodes.FindResourceNode(ctx, "node_oil_1")
	if err != nil {
		t.Fatal(err)
	}
	node.Amount = 99
	if err := nodes.SaveResourceNode(ctx, node); err != nil {
		t.Fatal(err)
	}
	if _, _, err := production.Start(ctx, "p1", string(well.ID), catalog.OilExtractionRecipeID); err == nil {
		t.Fatal("oil extraction started without enough deposit stock")
	}
	if _, err := resources.Tick(ctx, node.UpdatedAt.Add(time.Hour), 10); err != nil {
		t.Fatal(err)
	}
	updated, err := nodes.FindResourceNode(ctx, node.ID)
	if err != nil {
		t.Fatal(err)
	}
	if updated.Amount != 99 {
		t.Fatalf("oil was extracted without a production job: %d", updated.Amount)
	}
}

func TestDestroyedOilWellCancelsExtractionAndReturnsWorkers(t *testing.T) {
	ctx := context.Background()
	service, resources, buildings, nodes, _, well := oilFixture(t)
	if _, err := service.CompleteAt(ctx, well.ID, "p1", well.StartedAt.Add(11*time.Minute)); err != nil {
		t.Fatal(err)
	}
	production := NewProductionService(nodes, resources.economy, resources.log)
	production.SetBuildings(buildings)
	production.SetResources(resources)
	grantTestResources(t, ctx, resources.economy, "p1", economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 15})
	before, err := resources.economy.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	job, _, err := production.Start(ctx, "p1", string(well.ID), catalog.OilExtractionRecipeID)
	if err != nil {
		t.Fatal(err)
	}
	well, err = buildings.FindByID(ctx, well.ID)
	if err != nil {
		t.Fatal(err)
	}
	if _, _, err := buildings.DamageIfCurrent(ctx, well.ID, well.Health, well.Health, time.Now()); err != nil {
		t.Fatal(err)
	}
	node, err := nodes.FindResourceNode(ctx, "node_oil_1")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := resources.Tick(ctx, time.Now(), 10); err != nil {
		t.Fatal(err)
	}
	stopped, err := nodes.FindProductionJob(ctx, job.ID)
	if err != nil {
		t.Fatal(err)
	}
	after, err := resources.economy.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	if stopped.State != economy.ProductionCancelled || after.Items[economy.ResourcePopulation] != before.Items[economy.ResourcePopulation] {
		t.Fatalf("workers not returned after destruction: job=%s before=%d after=%d", stopped.State, before.Items[economy.ResourcePopulation], after.Items[economy.ResourcePopulation])
	}
	remaining, err := nodes.FindResourceNode(ctx, node.ID)
	if err != nil {
		t.Fatal(err)
	}
	if remaining.Amount != node.Amount {
		t.Fatalf("destroyed well consumed oil: %d -> %d", node.Amount, remaining.Amount)
	}
}

func oilFixture(t *testing.T) (*BuildingService, *ResourceService, *memory.BuildingRepo, *memory.EconomyRepo, *memory.WorldRepo, building.Building) {
	t.Helper()
	ctx := context.Background()
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	buildings, nodes, worlds := memory.NewBuildingRepo(), memory.NewEconomyRepo(), memory.NewWorldRepo()
	resources := NewResourceService(nodes, NewEconomyService(nodes, buildings, log), log)
	resources.SetOilWorld(worlds, buildings)
	service := NewBuildingService(buildings, worlds, log)
	service.SetResources(resources)
	if err := buildings.Create(ctx, building.Building{ID: "hall", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeTownHall, State: building.StateActive, Health: 100, Level: 1, Tile: world.Coord{X: 0, Y: 0}, Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
		t.Fatal(err)
	}
	well, err := service.Place(ctx, PlaceBuildingInput{PlayerID: player.ID("p1"), Type: building.TypeOilWell, Tile: world.Coord{X: 24, Y: 18}})
	if err != nil {
		t.Fatal(err)
	}
	return service, resources, buildings, nodes, worlds, well
}

func TestOilWellClaimsOnConstructionAndSaleReleases(t *testing.T) {
	ctx := context.Background()
	service, resources, buildings, nodes, _, well := oilFixture(t)
	if well.State != building.StateBuilding || well.Health != 220 {
		t.Fatalf("wrong construction state: %#v", well)
	}
	node, err := nodes.FindResourceNode(ctx, "node_oil_1")
	if err != nil {
		t.Fatal(err)
	}
	if node.OwnerID != "p1" || node.State != economy.NodeClaimed {
		t.Fatalf("oil was not claimed: %#v", node)
	}
	if _, err := resources.Claim(ctx, node.ID, "p2"); err == nil {
		t.Fatal("oil can be claimed without construction")
	}
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: "p1", Type: building.TypeOilWell, Tile: well.Tile}); err == nil {
		t.Fatal("second well accepted")
	}
	if err := service.Demolish(ctx, well.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	node, err = nodes.FindResourceNode(ctx, node.ID)
	if err != nil {
		t.Fatal(err)
	}
	if node.OwnerID != "" || node.State != economy.NodeNeutral || node.Amount != node.MaxAmount {
		t.Fatalf("sale kept ownership: %#v", node)
	}
	if err := buildings.Create(ctx, building.Building{ID: "hall-p2", MapID: DefaultWorldID, OwnerID: "p2", Type: building.TypeTownHall, State: building.StateActive, Health: 100, Level: 1, Tile: world.Coord{X: 1, Y: 0}, Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
		t.Fatal(err)
	}
	if _, err := service.Place(ctx, PlaceBuildingInput{PlayerID: "p2", Type: building.TypeOilWell, Tile: well.Tile}); err != nil {
		t.Fatalf("second player cannot claim freed oil: %v", err)
	}
	node, err = nodes.FindResourceNode(ctx, node.ID)
	if err != nil {
		t.Fatal(err)
	}
	if node.OwnerID != "p2" {
		t.Fatalf("new owner = %q", node.OwnerID)
	}
}

func TestDestroyedOilWellReleasesDeposit(t *testing.T) {
	ctx := context.Background()
	_, resources, buildings, nodes, _, well := oilFixture(t)
	if _, applied, err := buildings.DamageIfCurrent(ctx, well.ID, well.Health, well.Health, time.Now()); err != nil || !applied {
		t.Fatalf("damage: %v, applied=%v", err, applied)
	}
	if _, err := resources.Tick(ctx, time.Now().Add(time.Second), 10); err != nil {
		t.Fatal(err)
	}
	node, err := nodes.FindResourceNode(ctx, "node_oil_1")
	if err != nil {
		t.Fatal(err)
	}
	if node.OwnerID != "" || node.State != economy.NodeNeutral {
		t.Fatalf("destruction kept ownership: %#v", node)
	}
	if _, err := buildings.FindByID(ctx, well.ID); err == nil {
		t.Fatal("destroyed well still occupies deposit")
	}
}

func TestDepletedOilRespawnsElsewhereAfterFiveToTenMinutes(t *testing.T) {
	ctx := context.Background()
	service, resources, buildings, nodes, worlds, well := oilFixture(t)
	if _, err := service.CompleteAt(ctx, well.ID, "p1", well.StartedAt.Add(11*time.Minute)); err != nil {
		t.Fatal(err)
	}
	node, err := nodes.FindResourceNode(ctx, "node_oil_1")
	if err != nil {
		t.Fatal(err)
	}
	node.Amount = 100
	if err := nodes.SaveResourceNode(ctx, node); err != nil {
		t.Fatal(err)
	}
	production := NewProductionService(nodes, resources.economy, resources.log)
	production.SetBuildings(buildings)
	production.SetResources(resources)
	production.now = func() time.Time { return node.UpdatedAt }
	grantTestResources(t, ctx, resources.economy, "p1", economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 15})
	job, _, err := production.Start(ctx, "p1", string(well.ID), "oil_extraction")
	if err != nil {
		t.Fatal(err)
	}
	extractAt := job.CompletesAt
	if _, _, err := production.CompleteAt(ctx, "p1", job.ID, extractAt); err != nil {
		t.Fatal(err)
	}
	if _, err := resources.Tick(ctx, extractAt, 10); err != nil {
		t.Fatal(err)
	}
	node, err = nodes.FindResourceNode(ctx, node.ID)
	if err != nil {
		t.Fatal(err)
	}
	if node.State != economy.NodeDepleted || node.OwnerID != "" || node.RespawnAt == nil {
		t.Fatalf("oil not depleted: %#v", node)
	}
	if delay := node.RespawnAt.Sub(extractAt); delay < 5*time.Minute || delay > 10*time.Minute {
		t.Fatalf("respawn delay = %s", delay)
	}
	oldChunk, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(well.Tile))
	if err != nil {
		t.Fatal(err)
	}
	oldTile, _ := findTile(oldChunk, well.Tile)
	if oldTile.Terrain != world.TerrainGrass {
		t.Fatalf("old deposit remains: %s", oldTile.Terrain)
	}
	if _, err := buildings.FindByID(ctx, well.ID); err == nil {
		t.Fatal("depleted well remains")
	}
	var destination world.Coord
	found := false
	for x := 20; x < worldgen.WorldSizeTiles && !found; x++ {
		for y := 20; y < worldgen.WorldSizeTiles; y++ {
			coord := world.Coord{X: x, Y: y}
			chunk, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(coord))
			if err != nil {
				t.Fatal(err)
			}
			tile, _ := findTile(chunk, coord)
			if tile.Terrain == world.TerrainGrass && !tile.SafeZone {
				destination, found = coord, true
				break
			}
		}
	}
	if !found {
		t.Fatal("no grass destination")
	}
	index := 0
	resources.randomIntn = func(int) int {
		index++
		if index%2 == 1 {
			return destination.X
		}
		return destination.Y
	}
	if _, err := resources.Tick(ctx, *node.RespawnAt, 10); err != nil {
		t.Fatal(err)
	}
	node, err = nodes.FindResourceNode(ctx, node.ID)
	if err != nil {
		t.Fatal(err)
	}
	if node.State != economy.NodeNeutral || node.Tile != destination || node.Amount != node.MaxAmount {
		t.Fatalf("bad respawn: %#v", node)
	}
	newChunk, _, err := worlds.GetOrCreateChunk(ctx, DefaultWorldID, world.ChunkForTile(destination))
	if err != nil {
		t.Fatal(err)
	}
	newTile, _ := findTile(newChunk, destination)
	if newTile.Terrain != world.TerrainOilWell {
		t.Fatalf("new terrain = %s", newTile.Terrain)
	}
}
