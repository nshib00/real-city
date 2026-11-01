package service

import (
	"context"
	"errors"
	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"sync"
	"testing"
	"time"
)

type rejectProductionSchedule struct{ *memory.ActionRepo }

func (r rejectProductionSchedule) Append(context.Context, action.GameAction) error {
	return errors.New("queue unavailable")
}

func TestProductionQueueFailureRollsBackAndConcurrentCommandsCollectOnce(t *testing.T) {
	ctx := context.Background()
	buildings, repo, eco, s := newProductionPopulationTestServices()
	createActiveProductionBuilding(t, ctx, buildings, "production-race", "p1", building.TypeLumberYard, 1)
	before := setTestPopulation(t, ctx, repo, eco, "p1", 10)
	s.SetActionQueue(rejectProductionSchedule{memory.NewActionRepo()})
	if _, _, err := s.Start(ctx, "p1", "production-race", "planks_from_wood"); err == nil {
		t.Fatal("schedule failure ignored")
	}
	after, err := eco.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	if after.Items[economy.ResourceWood] != before.Items[economy.ResourceWood] || after.Items[economy.ResourcePopulation] != before.Items[economy.ResourcePopulation] {
		t.Fatal("rollback lost inputs/workers")
	}
	jobs, _ := repo.ListProductionJobs(ctx, "p1")
	if len(jobs) != 0 {
		t.Fatal("rolled-back job persisted")
	}
	s.SetActionQueue(memory.NewActionRepo())
	var wg sync.WaitGroup
	out := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, _, err := s.Start(ctx, "p1", "production-race", "planks_from_wood")
			out <- err
		}()
	}
	wg.Wait()
	close(out)
	success := 0
	for err := range out {
		if err == nil {
			success++
		}
	}
	if success != 1 {
		t.Fatal("duplicate production start", success)
	}
	jobs, _ = repo.ListProductionJobs(ctx, "p1")
	job := jobs[0]
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, _, err := s.CompleteAt(ctx, "p1", job.ID, job.CompletesAt.Add(time.Second)); err != nil {
				t.Error(err)
			}
		}()
	}
	wg.Wait()
	after, err = eco.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	if after.Items[economy.ResourcePlanks] != before.Items[economy.ResourcePlanks]+2 || after.Items[economy.ResourcePopulation] != before.Items[economy.ResourcePopulation] {
		t.Fatal("double output or workers", after.Items)
	}
}
