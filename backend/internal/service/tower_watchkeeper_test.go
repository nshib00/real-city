package service

import (
	"context"
	"errors"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
)

type watchkeeperFailRepo struct {
	*memory.BuildingRepo
	failUpdate bool
}

func (r *watchkeeperFailRepo) Update(ctx context.Context, item building.Building) error {
	if r.failUpdate {
		return errors.New("injected update failure")
	}
	return r.BuildingRepo.Update(ctx, item)
}

func TestTowerWatchkeeperReserveReleaseAndRollback(t *testing.T) {
	ctx := context.Background()
	repo := &watchkeeperFailRepo{BuildingRepo: memory.NewBuildingRepo()}
	economyRepo := memory.NewEconomyRepo()
	eco := NewEconomyService(economyRepo, repo, slog.Default())
	svc := NewBuildingService(repo, memory.NewWorldRepo(), slog.Default())
	svc.SetEconomy(eco)
	tower := building.Building{ID: "tower", OwnerID: "owner", Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100}
	if err := repo.Create(ctx, tower); err != nil {
		t.Fatal(err)
	}
	stock, err := eco.Inventory(ctx, "owner")
	if err != nil {
		t.Fatal(err)
	}
	stock.Items[economy.ResourcePopulation] = 1
	if err := economyRepo.SaveInventory(ctx, stock); err != nil {
		t.Fatal(err)
	}
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "other", true); err == nil {
		t.Fatal("non-owner assigned watchkeeper")
	}
	repo.failUpdate = true
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", true); err == nil {
		t.Fatal("expected update failure")
	}
	assertWatchkeeperPopulation(t, ctx, eco, repo, 1, false)
	repo.failUpdate = false
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", true); err != nil {
		t.Fatal(err)
	}
	assertWatchkeeperPopulation(t, ctx, eco, repo, 0, true)
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", true); err != nil {
		t.Fatal(err)
	}
	assertWatchkeeperPopulation(t, ctx, eco, repo, 0, true)
	repo.failUpdate = true
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", false); err == nil {
		t.Fatal("expected removal failure")
	}
	assertWatchkeeperPopulation(t, ctx, eco, repo, 0, true)
	repo.failUpdate = false
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", false); err != nil {
		t.Fatal(err)
	}
	assertWatchkeeperPopulation(t, ctx, eco, repo, 1, false)
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", true); err != nil {
		t.Fatal(err)
	}
	if err := svc.Demolish(ctx, tower.ID, "owner"); err != nil {
		t.Fatal(err)
	}
	stock, _ = eco.Inventory(ctx, "owner")
	if stock.Items[economy.ResourcePopulation] != 1 {
		t.Fatal("demolition did not release watchkeeper")
	}
}

func TestTowerWatchkeeperDestructionAndUpgrade(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewBuildingRepo()
	ecoRepo := memory.NewEconomyRepo()
	eco := NewEconomyService(ecoRepo, repo, slog.Default())
	svc := NewBuildingService(repo, memory.NewWorldRepo(), slog.Default())
	svc.SetEconomy(eco)
	tower := building.Building{ID: "tower", OwnerID: "owner", Type: building.TypeTower, Level: 1, State: building.StateActive, Health: 100, Footprint: building.Footprint{Width: 1, Height: 1}}
	if err := repo.Create(ctx, tower); err != nil {
		t.Fatal(err)
	}
	stock, _ := eco.Inventory(ctx, "owner")
	stock.Items[economy.ResourcePopulation] = 10
	if err := ecoRepo.SaveInventory(ctx, stock); err != nil {
		t.Fatal(err)
	}
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", true); err != nil {
		t.Fatal(err)
	}
	stock, _ = eco.Inventory(ctx, "owner")
	if stock.Items[economy.ResourcePopulation] != 9 {
		t.Fatal("watchkeeper not reserved")
	}
	next, ok := nextUpgradeTo(tower, "")
	if !ok {
		t.Fatal("tower upgrade missing")
	}
	for _, cost := range next.Cost {
		stock.Items[economy.ResourceType(cost.Resource)] += cost.Amount
	}
	if err := ecoRepo.SaveInventory(ctx, stock); err != nil {
		t.Fatal(err)
	}
	upgraded, err := svc.Upgrade(ctx, tower.ID, "owner")
	if err != nil {
		t.Fatal(err)
	}
	if !upgraded.TowerWatchkeeperAssigned || upgraded.State != building.StateBuilding {
		t.Fatalf("upgrade lost watchkeeper or remained active: %+v", upgraded)
	}
	stock, _ = eco.Inventory(ctx, "owner")
	if stock.Items[economy.ResourcePopulation] != 9-next.Population {
		t.Fatalf("upgrade population = %d", stock.Items[economy.ResourcePopulation])
	}
	if err := svc.Cancel(ctx, tower.ID, "owner"); err != nil {
		t.Fatal(err)
	}
	stock, _ = eco.Inventory(ctx, "owner")
	if stock.Items[economy.ResourcePopulation] != 10 {
		t.Fatal("cancel did not release builder and watchkeeper")
	}
	if err := repo.Create(ctx, tower); err != nil {
		t.Fatal(err)
	}
	if _, err := svc.SetTowerWatchkeeper(ctx, tower.ID, "owner", true); err != nil {
		t.Fatal(err)
	}
	before, _ := repo.FindByID(ctx, tower.ID)
	after := before
	after.Health, after.State = 0, building.StateRuined
	if err := svc.HandleDestruction(ctx, before, after, "", time.Now()); err != nil {
		t.Fatal(err)
	}
	stock, _ = eco.Inventory(ctx, "owner")
	stored, _ := repo.FindByID(ctx, tower.ID)
	if stock.Items[economy.ResourcePopulation] != 10 || stored.TowerWatchkeeperAssigned {
		t.Fatal("destruction did not release and clear watchkeeper")
	}
}

func assertWatchkeeperPopulation(t *testing.T, ctx context.Context, eco *EconomyService, repo *watchkeeperFailRepo, want int, assigned bool) {
	t.Helper()
	stock, err := eco.Inventory(ctx, "owner")
	if err != nil {
		t.Fatal(err)
	}
	item, err := repo.FindByID(ctx, "tower")
	if err != nil {
		t.Fatal(err)
	}
	if stock.Items[economy.ResourcePopulation] != want || item.TowerWatchkeeperAssigned != assigned {
		t.Fatalf("population=%d assigned=%v, want %d/%v", stock.Items[economy.ResourcePopulation], item.TowerWatchkeeperAssigned, want, assigned)
	}
}
