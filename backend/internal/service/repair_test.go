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

type failedRepairRepo struct {
	*memory.BuildingRepo
	fail bool
}

func (r *failedRepairRepo) CreateRepair(ctx context.Context, j building.RepairJob) error {
	if r.fail {
		return errors.New("injected repair insert failure")
	}
	return r.BuildingRepo.CreateRepair(ctx, j)
}
func TestRepairRollbackAndDestroyedTarget(t *testing.T) {
	ctx := context.Background()
	repo := &failedRepairRepo{BuildingRepo: memory.NewBuildingRepo(), fail: true}
	er := memory.NewEconomyRepo()
	eco := NewEconomyService(er, repo, slog.Default())
	svc := NewBuildingService(repo, memory.NewWorldRepo(), slog.Default())
	svc.SetEconomy(eco)
	b := building.Building{ID: "repair_target", OwnerID: "p1", Type: building.TypeStoneHouse, Level: 6, Health: 100, State: building.StateDamaged}
	if err := repo.Create(ctx, b); err != nil {
		t.Fatal(err)
	}
	quote := quoteRepair(b)
	grant := []economy.ResourceAmount{{Resource: economy.ResourcePopulation, Amount: 2}}
	for _, v := range quote.Cost {
		grant = append(grant, economy.ResourceAmount{Resource: v.Resource, Amount: v.Amount})
	}
	before := grantTestResources(t, withUncappedCoins(ctx), eco, "p1", grant...)
	if _, err := svc.Repair(ctx, b.ID, "p1"); err == nil {
		t.Fatal("expected insert error")
	}
	after, _ := eco.Inventory(ctx, "p1")
	for r, n := range before.Items {
		if after.Items[r] != n {
			t.Fatal("failed repair spent resources")
		}
	}
	repo.fail = false
	if _, err := svc.Repair(ctx, b.ID, "p1"); err != nil {
		t.Fatal(err)
	}
	job, _ := repo.PendingRepair(ctx, b.ID)
	b.Health = 0
	b.State = building.StateRuined
	if err := repo.Update(ctx, b); err != nil {
		t.Fatal(err)
	}
	if _, err := svc.CompleteRepairs(ctx, job.DueAt.Add(time.Second), 10); err != nil {
		t.Fatal(err)
	}
	stored, _ := repo.FindByID(ctx, b.ID)
	if stored.Health != 0 || stored.State != building.StateRuined {
		t.Fatal("repair resurrected destroyed target")
	}
	after, _ = eco.Inventory(ctx, "p1")
	if after.Items[economy.ResourcePopulation] != before.Items[economy.ResourcePopulation] {
		t.Fatal("workers not returned")
	}
	if n, err := svc.CompleteRepairs(ctx, job.DueAt.Add(time.Minute), 10); err != nil || n != 0 {
		t.Fatal("repair completed twice")
	}
}
