package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

func xpBuildingSpecs() []catalog.BuildingType {
	items := catalog.AllBuildings()
	for _, ruin := range catalog.RuinSpecs {
		items = append(items, ruin)
	}
	return items
}

func xpLevels(spec catalog.BuildingType) []catalog.BuildingUpgradeLevel {
	if len(spec.UpgradeLevels) > 0 {
		return spec.UpgradeLevels
	}
	return []catalog.BuildingUpgradeLevel{{Level: spec.Level}}
}

func TestEveryBuildingLevelAwardsCompletionAndDestructionExactlyOnce(t *testing.T) {
	for _, spec := range xpBuildingSpecs() {
		for _, level := range xpLevels(spec) {
			t.Run(fmt.Sprintf("%s/%d", spec.Type, level.Level), func(t *testing.T) {
				ctx, now := context.Background(), time.Now().UTC()
				players, xp := newExperienceTestPlayer(t)
				buildings := memory.NewBuildingRepo()
				service := NewBuildingService(buildings, nil, slog.Default())
				service.SetExperience(xp)
				item := building.Building{ID: "target", OwnerID: "p1", Type: spec.Type, Level: level.Level, Health: 1, State: building.StateBuilding, CompletesAt: &now}
				if err := buildings.Create(ctx, item); err != nil {
					t.Fatal(err)
				}
				for range 2 {
					if _, err := service.CompleteAt(ctx, item.ID, "p1", now); err != nil {
						t.Fatal(err)
					}
				}
				want := catalog.ExperienceForBuilding(spec.Type, level.Level)
				if got := playerXP(t, players); got != want.Completion {
					t.Fatalf("completion XP %d, want %d", got, want.Completion)
				}
				item, _ = buildings.FindByID(ctx, item.ID)
				item.OwnerID = "enemy"
				if err := buildings.Update(ctx, item); err != nil {
					t.Fatal(err)
				}
				combat := NewCombatService(NewMonsterService(memory.NewMonsterRepo(), slog.Default()), slog.Default())
				combat.SetBuildingService(service)
				combat.SetPvPDependencies(buildings, nil, nil)
				payload, _ := json.Marshal(map[string]string{"owner_id": "enemy", "weapon": string(economy.ResourceThrowingKnives)})
				attack := action.GameAction{ID: "hit", Actor: action.ObjectRef{ID: "p1", Type: "player"}, Target: action.ObjectRef{ID: "target", Type: "building"}, Payload: payload}
				for range 2 {
					if err := combat.ResolveWeapon(ctx, attack); err != nil {
						t.Fatal(err)
					}
				}
				if got := playerXP(t, players); got != want.Completion+want.Destruction {
					t.Fatalf("XP %d, want %d", got, want.Completion+want.Destruction)
				}
				_, err := buildings.FindByID(ctx, item.ID)
				if spec.Type == building.TypeOilWell || catalog.IsRuin(spec.Type) {
					if err == nil {
						t.Fatal("destroyed special building still exists")
					}
				} else {
					destroyed, err := buildings.FindByID(ctx, item.ID)
					if err != nil || destroyed.Health != 0 || destroyed.State != building.StateRuined {
						t.Fatalf("not destroyed: %+v %v", destroyed, err)
					}
				}
			})
		}
	}
}

func TestBuildingUpgradeAwardsDestinationSpecification(t *testing.T) {
	for _, tc := range []struct {
		kind   building.Type
		level  int
		target building.Type
	}{
		{building.TypeDugout, 4, building.TypeDugout},
		{building.TypeWoodHouse, 6, building.TypeStoneHouse},
		{building.TypeRoad, 1, building.TypeStandardRoad},
	} {
		t.Run(string(tc.kind), func(t *testing.T) {
			ctx, now := context.Background(), time.Now().UTC()
			players, xp := newExperienceTestPlayer(t)
			buildings := memory.NewBuildingRepo()
			service := NewBuildingService(buildings, nil, slog.Default())
			service.SetExperience(xp)
			service.SetNowForTest(func() time.Time { return now })
			if err := buildings.Create(ctx, building.Building{ID: "upgrade", OwnerID: "p1", Type: tc.kind, Level: tc.level, State: building.StateActive, Health: 100, Footprint: building.Footprint{Width: 1, Height: 1}}); err != nil {
				t.Fatal(err)
			}
			item, err := service.UpgradeTo(ctx, "upgrade", "p1", tc.target)
			if err != nil {
				t.Fatal(err)
			}
			if got := playerXP(t, players); got != 0 {
				t.Fatal("XP awarded before completion")
			}
			if _, err := service.CompleteAt(ctx, item.ID, "p1", item.CompletesAt.Add(time.Second)); err != nil {
				t.Fatal(err)
			}
			if got, want := playerXP(t, players), catalog.ExperienceForBuilding(item.Type, item.Level).Completion; got != want {
				t.Fatalf("XP %d, want %d", got, want)
			}
		})
	}
}

func TestFreeTownHallCannotBeRebuiltForUnlimitedXP(t *testing.T) {
	ctx, now := context.Background(), time.Now().UTC()
	players, xp := newExperienceTestPlayer(t)
	buildings := memory.NewBuildingRepo()
	bs := NewBuildingService(buildings, nil, slog.Default())
	bs.SetExperience(xp)
	for _, id := range []building.ID{"first-hall", "rebuilt-hall"} {
		if err := buildings.Create(ctx, building.Building{ID: id, OwnerID: "p1", Type: building.TypeTownHall, Level: 1, State: building.StateBuilding}); err != nil {
			t.Fatal(err)
		}
		if _, err := bs.CompleteAt(ctx, id, "p1", now); err != nil {
			t.Fatal(err)
		}
		if err := bs.Demolish(ctx, id, "p1"); err != nil {
			t.Fatal(err)
		}
	}
	if got, want := playerXP(t, players), catalog.ExperienceForBuilding(building.TypeTownHall, 1).Completion; got != want {
		t.Fatalf("free hall XP %d, want %d", got, want)
	}
}

type failingBattleXPRepo struct {
	*memory.PlayerRepo
	fail bool
}

func (r *failingBattleXPRepo) AwardXPEvent(ctx context.Context, id player.ID, amount int, reason, key string) (bool, error) {
	applied, err := r.PlayerRepo.AwardXPEvent(ctx, id, amount, reason, key)
	if err == nil && r.fail {
		return false, errors.New("injected XP failure after write")
	}
	return applied, err
}

func TestLethalWeaponRollsBackOnXPFailureAndCanRetry(t *testing.T) {
	for _, delayed := range []bool{false, true} {
		t.Run(fmt.Sprint(delayed), func(t *testing.T) {
			s, buildings, inventory, actions := pvpFixture(t)
			ctx := context.Background()
			players := &failingBattleXPRepo{PlayerRepo: memory.NewPlayerRepo(), fail: true}
			now := s.now()
			if err := players.Create(ctx, player.Player{ID: "attacker", Email: "a@example.com", Name: "attacker", Status: player.StatusActive, Profile: player.DefaultProfile("attacker", now)}); err != nil {
				t.Fatal(err)
			}
			bs := NewBuildingService(buildings, nil, slog.Default())
			bs.SetExperience(NewExperienceService(players, slog.Default()))
			s.SetBuildingService(bs)
			target, _ := buildings.FindByID(ctx, "target")
			target.Health = 1
			if err := buildings.Update(ctx, target); err != nil {
				t.Fatal(err)
			}
			weapon := economy.ResourceThrowingKnives
			if delayed {
				weapon = economy.ResourceBlackpowderBomb
			}
			before, _ := inventory.GetInventory(ctx, "attacker", 10000)
			attack, err := s.UseBuildingWeapon(ctx, "target", "attacker", weapon, "xp-failure-key")
			if delayed {
				if err != nil {
					t.Fatal(err)
				}
				due, err := actions.FetchDue(ctx, attack.DueAt, 10, time.Minute)
				if err != nil || len(due) != 1 {
					t.Fatalf("due actions: %+v %v", due, err)
				}
				err = s.ResolveWeapon(ctx, due[0])
				if err == nil {
					t.Fatal("expected XP failure")
				}
				players.fail = false
				if err := s.ResolveWeapon(ctx, due[0]); err != nil {
					t.Fatal(err)
				}
				if err := s.ResolveWeapon(ctx, due[0]); err != nil {
					t.Fatal(err)
				}
			} else {
				if err == nil {
					t.Fatal("expected XP failure")
				}
				remaining, _ := inventory.GetInventory(ctx, "attacker", 10000)
				if remaining.Items[weapon] != before.Items[weapon] {
					t.Fatal("failed attack consumed weapon")
				}
				target, _ = buildings.FindByID(ctx, "target")
				profile, _ := players.FindByID(ctx, "attacker")
				if target.Health != 1 || profile.Profile.XP != 0 {
					t.Fatal("failed lethal hit was not rolled back")
				}
				players.fail = false
				if _, err := s.UseBuildingWeapon(ctx, "target", "attacker", weapon, "xp-failure-key"); err != nil {
					t.Fatal(err)
				}
			}
			profile, _ := players.FindByID(ctx, "attacker")
			if got, want := profile.Profile.XP, catalog.ExperienceForBuilding(target.Type, target.Level).Destruction; got != want {
				t.Fatalf("XP %d, want %d", got, want)
			}
		})
	}
}

func TestAllFieldLevelsAwardNormalAndSuperHarvestXP(t *testing.T) {
	for _, spec := range catalog.AllBuildings() {
		if !economy.IsFieldCropBuildingType(string(spec.Type)) {
			continue
		}
		for _, level := range xpLevels(spec) {
			for _, super := range []bool{false, true} {
				t.Run(fmt.Sprintf("%s/%d/super=%t", spec.Type, level.Level, super), func(t *testing.T) {
					ctx, now := context.Background(), time.Now().UTC()
					players, xp := newExperienceTestPlayer(t)
					buildings, inventory := memory.NewBuildingRepo(), memory.NewEconomyRepo()
					fields := NewFieldService(NewEconomyService(inventory, buildings, slog.Default()), buildings)
					fields.SetExperience(xp)
					fields.SetNowForTest(func() time.Time { return now })
					crop, _ := economy.FieldCropForBuildingType(string(spec.Type), level.Level, super)
					ready := now.Add(-time.Second)
					item := building.Building{ID: "field", OwnerID: "p1", Type: spec.Type, Level: level.Level, State: building.StateActive, FieldStage: len(crop.Growth), FieldStageReadyAt: &ready, FieldSuperCrop: super}
					if err := buildings.Create(ctx, item); err != nil {
						t.Fatal(err)
					}
					if _, _, err := fields.HarvestField(ctx, "p1", item.ID); err != nil {
						t.Fatal(err)
					}
					want := catalog.ExperienceForBuilding(spec.Type, level.Level).Work
					if super {
						want *= 3
					}
					if got := playerXP(t, players); got != want {
						t.Fatalf("XP %d, want %d", got, want)
					}
					if _, _, err := fields.HarvestField(ctx, "p1", item.ID); err == nil {
						t.Fatal("duplicate harvest accepted")
					}
					if got := playerXP(t, players); got != want {
						t.Fatal("duplicate harvest gave XP")
					}
				})
			}
		}
	}
}

func TestAllProductionBuildingsAwardSpecificationXP(t *testing.T) {
	for _, recipe := range catalog.ProductionCatalog() {
		spec, _ := catalog.GetBuilding(building.Type(recipe.BuildingType))
		for _, level := range xpLevels(spec) {
			if level.Level < recipe.RequiredLevel {
				continue
			}
			t.Run(fmt.Sprintf("%s/%d", recipe.ID, level.Level), func(t *testing.T) {
				ctx, now := context.Background(), time.Now().UTC()
				players, xp := newExperienceTestPlayer(t)
				buildings, inventory := memory.NewBuildingRepo(), memory.NewEconomyRepo()
				if err := buildings.Create(ctx, building.Building{ID: "factory", OwnerID: "p1", Type: spec.Type, Level: level.Level, Health: 100, State: building.StateActive}); err != nil {
					t.Fatal(err)
				}
				job := economy.ProductionJob{ID: "job", PlayerID: "p1", BuildingID: "factory", RecipeID: recipe.ID, State: economy.ProductionReady, CompletesAt: now}
				if err := inventory.SaveProductionJob(ctx, job); err != nil {
					t.Fatal(err)
				}
				production := NewProductionService(inventory, NewEconomyService(inventory, buildings, slog.Default()), slog.Default())
				production.SetBuildings(buildings)
				production.SetExperience(xp)
				for range 2 {
					if _, _, err := production.CompleteAt(ctx, "p1", job.ID, now); err != nil {
						t.Fatal(err)
					}
				}
				if got, want := playerXP(t, players), catalog.ExperienceForBuilding(spec.Type, level.Level).Work; got != want {
					t.Fatalf("XP %d, want %d", got, want)
				}
			})
		}
	}
}

func TestDestructionCancelsProductionAndReleasesOnlyBusyWorkers(t *testing.T) {
	ctx := context.Background()
	players, xp := newExperienceTestPlayer(t)
	buildings, inventory := memory.NewBuildingRepo(), memory.NewEconomyRepo()
	econ := NewEconomyService(inventory, buildings, slog.Default())
	bs := NewBuildingService(buildings, nil, slog.Default())
	bs.SetEconomy(econ)
	bs.SetExperience(xp)
	item := building.Building{ID: "factory", OwnerID: "enemy", Type: building.TypeGlassWorkshop, Level: 12, State: building.StateActive, Health: 1}
	if err := buildings.Create(ctx, item); err != nil {
		t.Fatal(err)
	}
	for _, job := range []economy.ProductionJob{
		{ID: "running", PlayerID: "enemy", BuildingID: "factory", RecipeID: "glass_batch", State: economy.ProductionRunning},
		{ID: "ready", PlayerID: "enemy", BuildingID: "factory", RecipeID: "glass_batch", State: economy.ProductionReady},
	} {
		if err := inventory.SaveProductionJob(ctx, job); err != nil {
			t.Fatal(err)
		}
	}
	before, _ := inventory.GetInventory(ctx, "enemy", 10000)
	if err := buildings.CreateRepair(ctx, building.RepairJob{ID: "repair", BuildingID: item.ID, PlayerID: "enemy", Workers: 1, Status: "pending"}); err != nil {
		t.Fatal(err)
	}
	combat := NewCombatService(NewMonsterService(memory.NewMonsterRepo(), slog.Default()), slog.Default())
	combat.SetBuildingService(bs)
	combat.SetPvPDependencies(buildings, nil, nil)
	payload := []byte(`{"owner_id":"enemy","weapon":"throwing_knives"}`)
	hit := action.GameAction{Actor: action.ObjectRef{ID: "p1"}, Target: action.ObjectRef{ID: "factory", Type: "building"}, Payload: payload}
	for range 2 {
		if err := combat.ResolveWeapon(ctx, hit); err != nil {
			t.Fatal(err)
		}
	}
	jobs, _ := inventory.ListProductionJobs(ctx, "enemy")
	for _, job := range jobs {
		if job.State != economy.ProductionCancelled {
			t.Fatal("production survived destruction")
		}
	}
	production := NewProductionService(inventory, econ, slog.Default())
	production.SetBuildings(buildings)
	production.SetExperience(xp)
	if _, err := production.ReadyAt(ctx, "enemy", "running", time.Now().Add(time.Hour)); err != nil {
		t.Fatalf("queued completion must ignore cancelled production: %v", err)
	}
	if _, _, err := production.CompleteAt(ctx, "enemy", "ready", time.Now()); err == nil {
		t.Fatal("destroyed building yielded cancelled production")
	}
	after, _ := inventory.GetInventory(ctx, "enemy", 10000)
	recipe, _ := catalog.RecipeForBuildingLevel("glass_batch", 12)
	if after.Items[economy.ResourcePopulation]-before.Items[economy.ResourcePopulation] != recipe.Workers+1 {
		t.Fatal("workers not returned exactly once")
	}
	if _, err := buildings.PendingRepair(ctx, item.ID); err == nil {
		t.Fatal("repair survived destruction")
	}
	if got := playerXP(t, players); got != 497681 {
		t.Fatalf("late destruction XP %d, want 497681", got)
	}
	if err := buildings.Update(ctx, item); err == nil {
		t.Fatal("stale update resurrected destroyed building")
	}
}

func TestDestructionXPRequiresEnemyAndLethalHit(t *testing.T) {
	s, buildings, _, _ := pvpFixture(t)
	ctx := context.Background()
	players := memory.NewPlayerRepo()
	if err := players.Create(ctx, player.Player{ID: "attacker", Email: "a@example.com", Name: "attacker", Status: player.StatusActive}); err != nil {
		t.Fatal(err)
	}
	bs := NewBuildingService(buildings, nil, slog.Default())
	bs.SetExperience(NewExperienceService(players, slog.Default()))
	s.SetBuildingService(bs)
	for _, tc := range []struct{ target, owner string }{
		{"source", "attacker"},
		{"target", "previous-owner"},
		{"target", "defender"},
	} {
		payload, _ := json.Marshal(map[string]string{"owner_id": tc.owner, "weapon": "throwing_knives"})
		if err := s.ResolveWeapon(ctx, action.GameAction{Actor: action.ObjectRef{ID: "attacker"}, Target: action.ObjectRef{ID: tc.target, Type: "building"}, Payload: payload}); err != nil {
			t.Fatal(err)
		}
	}
	profile, _ := players.FindByID(ctx, "attacker")
	if profile.Profile.XP != 0 {
		t.Fatal("self, changed owner or nonlethal hit gave XP")
	}
	self, _ := buildings.FindByID(ctx, "source")
	if self.Health != 1000 {
		t.Fatal("own building was damaged")
	}
	target, _ := buildings.FindByID(ctx, "target")
	if target.Health != 920 {
		t.Fatalf("target HP %d, want 920", target.Health)
	}
}

func TestConcurrentLastHitsAwardOnlyOneAttacker(t *testing.T) {
	ctx := context.Background()
	players, buildings := memory.NewPlayerRepo(), memory.NewBuildingRepo()
	for _, id := range []player.ID{"first", "second"} {
		if err := players.Create(ctx, player.Player{ID: id, Email: string(id) + "@example.com", Name: string(id), Status: player.StatusActive}); err != nil {
			t.Fatal(err)
		}
	}
	target := building.Building{ID: "target", OwnerID: "enemy", Type: building.TypeModernWall, Level: 13, State: building.StateActive, Health: 1}
	if err := buildings.Create(ctx, target); err != nil {
		t.Fatal(err)
	}
	bs := NewBuildingService(buildings, nil, slog.Default())
	bs.SetExperience(NewExperienceService(players, slog.Default()))
	s := NewCombatService(NewMonsterService(memory.NewMonsterRepo(), slog.Default()), slog.Default())
	s.SetBuildingService(bs)
	s.SetPvPDependencies(buildings, nil, nil)
	results := make(chan error, 2)
	for _, id := range []string{"first", "second"} {
		go func(actor string) {
			results <- s.ResolveWeapon(ctx, action.GameAction{Actor: action.ObjectRef{ID: actor}, Target: action.ObjectRef{ID: "target", Type: "building"}, Payload: []byte(`{"owner_id":"enemy","weapon":"throwing_knives"}`)})
		}(id)
	}
	for range 2 {
		if err := <-results; err != nil {
			t.Fatal(err)
		}
	}
	first, _ := players.FindByID(ctx, "first")
	second, _ := players.FindByID(ctx, "second")
	if first.Profile.XP+second.Profile.XP != 493817 || (first.Profile.XP != 0 && second.Profile.XP != 0) {
		t.Fatalf("last hit XP: %d + %d", first.Profile.XP, second.Profile.XP)
	}
}

func TestPvPDestructionReleasesOilDepositAndProductionWorkers(t *testing.T) {
	ctx := context.Background()
	bs, resources, buildings, inventory, _, well := oilFixture(t)
	if _, err := bs.CompleteAt(ctx, well.ID, "p1", well.CompletesAt.Add(time.Second)); err != nil {
		t.Fatal(err)
	}
	bs.SetEconomy(resources.economy)
	players := memory.NewPlayerRepo()
	if err := players.Create(ctx, player.Player{ID: "attacker", Email: "attacker@example.com", Name: "attacker", Status: player.StatusActive}); err != nil {
		t.Fatal(err)
	}
	bs.SetExperience(NewExperienceService(players, slog.Default()))
	grantTestResources(t, ctx, resources.economy, "p1", economy.ResourceAmount{Resource: economy.ResourcePopulation, Amount: 15})
	production := NewProductionService(inventory, resources.economy, slog.Default())
	production.SetBuildings(buildings)
	production.SetResources(resources)
	job, _, err := production.Start(ctx, "p1", string(well.ID), catalog.OilExtractionRecipeID)
	if err != nil {
		t.Fatal(err)
	}
	before, _ := inventory.GetInventory(ctx, "p1", 10000)
	well, _ = buildings.FindByID(ctx, well.ID)
	well.Health = 1
	if err := buildings.Update(ctx, well); err != nil {
		t.Fatal(err)
	}
	combat := NewCombatService(NewMonsterService(memory.NewMonsterRepo(), slog.Default()), slog.Default())
	combat.SetPvPDependencies(buildings, nil, resources)
	combat.SetBuildingService(bs)
	hit := action.GameAction{Actor: action.ObjectRef{ID: "attacker"}, Target: action.ObjectRef{ID: string(well.ID), Type: "building"}, Payload: []byte(`{"owner_id":"p1","weapon":"throwing_knives"}`)}
	for range 2 {
		if err := combat.ResolveWeapon(ctx, hit); err != nil {
			t.Fatal(err)
		}
	}
	node, err := inventory.FindResourceNode(ctx, "node_oil_1")
	if err != nil || node.OwnerID != "" || node.State != economy.NodeNeutral {
		t.Fatalf("oil node: %+v %v", node, err)
	}
	if _, err := buildings.FindByID(ctx, well.ID); err == nil {
		t.Fatal("destroyed oil well still exists")
	}
	stopped, _ := inventory.FindProductionJob(ctx, job.ID)
	if stopped.State != economy.ProductionCancelled {
		t.Fatal("oil extraction not cancelled")
	}
	after, _ := inventory.GetInventory(ctx, "p1", 10000)
	if after.Items[economy.ResourcePopulation]-before.Items[economy.ResourcePopulation] != 15 {
		t.Fatal("oil workers not returned exactly once")
	}
	profile, _ := players.FindByID(ctx, "attacker")
	if profile.Profile.XP != catalog.ExperienceForBuilding(building.TypeOilWell, well.Level).Destruction {
		t.Fatal("wrong oil destruction XP")
	}
}
