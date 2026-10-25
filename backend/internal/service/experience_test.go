package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func newExperienceTestPlayer(t *testing.T) (*memory.PlayerRepo, *ExperienceService) {
	t.Helper()
	repo := memory.NewPlayerRepo()
	now := time.Now().UTC()
	item := player.Player{ID: "p1", Email: "xp@example.com", Name: "XP Player", Status: player.StatusActive, Profile: player.DefaultProfile("XP Player", now), CreatedAt: now, UpdatedAt: now}
	if err := repo.Create(context.Background(), item); err != nil {
		t.Fatal(err)
	}
	return repo, NewExperienceService(repo, slog.Default())
}

func playerXP(t *testing.T, repo *memory.PlayerRepo) int {
	t.Helper()
	item, err := repo.FindByID(context.Background(), "p1")
	if err != nil {
		t.Fatal(err)
	}
	return item.Profile.XP
}

func TestExperienceAwardIsIdempotentAndLevelsPlayer(t *testing.T) {
	repo, experience := newExperienceTestPlayer(t)
	for _, key := range []string{"first", "first", "second"} {
		if err := experience.Award(context.Background(), "p1", 100, "test", key); err != nil {
			t.Fatal(err)
		}
	}
	item, err := repo.FindByID(context.Background(), "p1")
	if err != nil {
		t.Fatal(err)
	}
	if item.Profile.XP != 200 || item.Profile.Level != 2 {
		t.Fatalf("expected 200 XP and level 2, got %d XP and level %d", item.Profile.XP, item.Profile.Level)
	}
}

func TestBuildingCompletionUsesDocumentedXPOnce(t *testing.T) {
	ctx := context.Background()
	repo, experience := newExperienceTestPlayer(t)
	buildings := memory.NewBuildingRepo()
	now := time.Now().UTC()
	item := building.Building{ID: "seed-1", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeSeedGarden, Level: 1, State: building.StateBuilding, CompletesAt: &now, Footprint: building.Footprint{Width: 1, Height: 1}}
	if err := buildings.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	service := NewBuildingService(buildings, memory.NewWorldRepo(), slog.Default())
	service.SetExperience(experience)
	for range 2 {
		if _, err := service.CompleteAt(ctx, item.ID, "p1", now.Add(time.Second)); err != nil {
			t.Fatal(err)
		}
	}
	if got := playerXP(t, repo); got != 12 {
		t.Fatalf("expected 12 XP from seed garden specification, got %d", got)
	}
}

func TestForestChopAwardsOneXPPerPhase(t *testing.T) {
	ctx := context.Background()
	repo, experience := newExperienceTestPlayer(t)
	coord := world.Coord{X: 2, Y: 2}
	chunk := world.ChunkForTile(coord)
	worlds := &forestWorldRepo{chunk: world.Chunk{MapID: DefaultWorldID, Coord: chunk, Tiles: []world.Tile{{MapID: DefaultWorldID, Chunk: chunk, Coord: coord, Terrain: world.TerrainForest, ForestDensity: 3}}}}
	service := NewForestService(worlds, NewEconomyService(memory.NewEconomyRepo(), nil, slog.Default()), slog.Default())
	service.SetExperience(experience)
	for range 3 {
		if _, err := service.Chop(ctx, "p1", coord); err != nil {
			t.Fatal(err)
		}
	}
	if got := playerXP(t, repo); got != 3 {
		t.Fatalf("expected 3 XP for fully chopped forest, got %d", got)
	}
}

func TestMonsterKillAwardsXPOnlyOnDeath(t *testing.T) {
	ctx := context.Background()
	repo, experience := newExperienceTestPlayer(t)
	monsters := memory.NewMonsterRepo()
	item, err := monsters.FindByID(ctx, "monster_roamer_1")
	if err != nil {
		t.Fatal(err)
	}
	item.Health = 40
	if err := monsters.Update(ctx, item); err != nil {
		t.Fatal(err)
	}
	service := NewMonsterService(monsters, slog.Default())
	service.SetExperience(experience)
	if _, _, err := service.Attack(ctx, item.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	if got := playerXP(t, repo); got != 0 {
		t.Fatalf("expected no XP before kill, got %d", got)
	}
	killed, _, err := service.Attack(ctx, item.ID, "p1")
	if err != nil || killed.State != monster.StateDead {
		t.Fatalf("expected dead monster, got %#v, %v", killed, err)
	}
	if got := playerXP(t, repo); got != 36 {
		t.Fatalf("expected 36 XP for roamer kill, got %d", got)
	}
	if _, _, err := service.Attack(ctx, item.ID, "p1"); err == nil || playerXP(t, repo) != 36 {
		t.Fatal("repeated attack must not grant more XP")
	}
}

func TestFieldHarvestAwardsDocumentedXP(t *testing.T) {
	for _, superCrop := range []bool{false, true} {
		ctx := context.Background()
		repo, experience := newExperienceTestPlayer(t)
		buildings := memory.NewBuildingRepo()
		now := time.Now().UTC()
		crop, _ := economy.FieldCropForBuildingType(string(building.TypeSeedGarden), 1, superCrop)
		readyAt := now.Add(-time.Second)
		item := building.Building{ID: "seed-harvest", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeSeedGarden, Level: 1, State: building.StateActive, FieldStage: len(crop.Growth), FieldStageReadyAt: &readyAt, FieldSuperCrop: superCrop}
		if err := buildings.Create(ctx, item); err != nil {
			t.Fatal(err)
		}
		service := NewFieldService(NewEconomyService(memory.NewEconomyRepo(), buildings, slog.Default()), buildings)
		service.SetExperience(experience)
		if _, _, err := service.HarvestField(ctx, "p1", item.ID); err != nil {
			t.Fatal(err)
		}
		want := 2
		if superCrop {
			want = 6
		}
		if got := playerXP(t, repo); got != want {
			t.Fatalf("super=%t: expected %d XP, got %d", superCrop, want, got)
		}
		if _, _, err := service.HarvestField(ctx, "p1", item.ID); err == nil || playerXP(t, repo) != want {
			t.Fatal("repeated harvest must not grant more XP")
		}
	}
}

func TestProductionCollectionAwardsDocumentedXP(t *testing.T) {
	ctx := context.Background()
	repo, experience := newExperienceTestPlayer(t)
	buildings := memory.NewBuildingRepo()
	if err := buildings.Create(ctx, building.Building{ID: "glass-1", MapID: DefaultWorldID, OwnerID: "p1", Type: building.TypeGlassWorkshop, Level: 1, State: building.StateActive}); err != nil {
		t.Fatal(err)
	}
	economyRepo := memory.NewEconomyRepo()
	now := time.Now().UTC()
	job := economy.ProductionJob{ID: "job-glass-1", PlayerID: "p1", BuildingID: "glass-1", RecipeID: "glass_batch", State: economy.ProductionReady, CompletesAt: now.Add(-time.Second)}
	if err := economyRepo.SaveProductionJob(ctx, job); err != nil {
		t.Fatal(err)
	}
	service := NewProductionService(economyRepo, NewEconomyService(economyRepo, buildings, slog.Default()), slog.Default())
	service.SetBuildings(buildings)
	service.SetExperience(experience)
	for range 2 {
		if _, _, err := service.CompleteAt(ctx, "p1", job.ID, now); err != nil {
			t.Fatal(err)
		}
	}
	if got := playerXP(t, repo); got != 16 {
		t.Fatalf("expected 16 XP for glass workshop work, got %d", got)
	}
}

func TestResourceNodeClaimAndHarvestAwardXP(t *testing.T) {
	ctx := context.Background()
	repo, experience := newExperienceTestPlayer(t)
	economyRepo := memory.NewEconomyRepo()
	service := NewResourceService(economyRepo, NewEconomyService(economyRepo, nil, slog.Default()), slog.Default())
	service.SetExperience(experience)
	for range 2 {
		if _, err := service.Claim(ctx, "node_wood_1", "p1"); err != nil {
			t.Fatal(err)
		}
	}
	if got := playerXP(t, repo); got != 5 {
		t.Fatalf("expected 5 XP for first claim only, got %d", got)
	}
	if _, _, err := service.Harvest(ctx, "node_wood_1", "p1"); err != nil {
		t.Fatal(err)
	}
	if got := playerXP(t, repo); got != 6 {
		t.Fatalf("expected 1 XP for harvesting, got total %d", got)
	}
}

func TestBuildingXPMatchesDocumentedExamples(t *testing.T) {
	cases := []struct {
		kind  building.Type
		level int
		want  catalog.BuildingXP
	}{
		{building.TypeFlaxField, 3, catalog.BuildingXP{Completion: 68, Work: 4, Destruction: 560}},
		{building.TypeGlassWorkshop, 9, catalog.BuildingXP{Completion: 6557, Work: 70, Destruction: 297600}},
		{building.TypeMine, 1, catalog.BuildingXP{Completion: 60, Work: 8, Destruction: 420}},
		{building.TypeRopeYard, 8, catalog.BuildingXP{Completion: 1220, Work: 42, Destruction: 23000}},
		{building.TypeDugout, 1, catalog.BuildingXP{}},
	}
	for _, testCase := range cases {
		if got := catalog.ExperienceForBuilding(testCase.kind, testCase.level); got != testCase.want {
			t.Fatalf("XP for %s level %d: got %#v, want %#v", testCase.kind, testCase.level, got, testCase.want)
		}
	}
}
