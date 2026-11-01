package service

import (
	"context"
	"log/slog"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"sync"
	"testing"
)

func TestCollectAndDestructionHaveOneSerializableOutcome(t *testing.T) {
	ctx := context.Background()
	buildings, repo, eco, production := newProductionPopulationTestServices()
	createActiveProductionBuilding(t, ctx, buildings, "doomed", "p1", building.TypeLumberYard, 1)
	before := setTestPopulation(t, ctx, repo, eco, "p1", 10)
	job, _, err := production.Start(ctx, "p1", "doomed", "planks_from_wood")
	if err != nil {
		t.Fatal(err)
	}
	s := NewBuildingService(buildings, nil, slog.Default())
	s.SetEconomy(eco)
	var wg sync.WaitGroup
	var collectErr, destroyErr error
	wg.Add(2)
	go func() { defer wg.Done(); _, _, collectErr = production.CompleteAt(ctx, "p1", job.ID, job.CompletesAt) }()
	go func() {
		defer wg.Done()
		destroyErr = s.DestructionTransaction(ctx, nil, func(ctx context.Context) error {
			b, err := buildings.FindByID(ctx, "doomed")
			if err != nil {
				return err
			}
			after := b
			after.Health = 0
			after.State = building.StateRuined
			return s.HandleDestruction(ctx, b, after, "", job.CompletesAt)
		})
	}()
	wg.Wait()
	if destroyErr != nil {
		t.Fatal(destroyErr)
	}
	after, err := eco.Inventory(ctx, "p1")
	if err != nil {
		t.Fatal(err)
	}
	expected := before.Items[economy.ResourcePlanks]
	if collectErr == nil {
		expected += 2
	}
	if after.Items[economy.ResourcePlanks] != expected || after.Items[economy.ResourcePopulation] != before.Items[economy.ResourcePopulation] {
		t.Fatal("nonserializable harvest/destruction", after.Items, collectErr)
	}
	if _, _, err := production.CompleteAt(ctx, "p1", job.ID, job.CompletesAt); collectErr != nil && err == nil {
		t.Fatal("destroyed job collected later")
	}
}
