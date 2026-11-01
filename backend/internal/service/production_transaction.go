package service

import (
	"context"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"time"
)

func (s *ProductionService) SetUnitOfWork(uow UnitOfWork) { s.uow = uow }

func (s *ProductionService) transaction(ctx context.Context, buildingID string, fn func(context.Context) error) error {
	uow := s.uow
	if _, ok := uow.(snapshotUnitOfWork); ok {
		uow = nil
	}
	if uow == nil {
		repos := []any{s.repo, s.buildings, s.actions}
		if s.experience != nil {
			repos = append(repos, s.experience.players)
		}
		uow = snapshotUnitOfWork{repos}
	}
	return transactional(ctx, uow, func(ctx context.Context) error {
		if locker, ok := s.buildings.(interface {
			LockForAction(context.Context, building.ID) error
		}); ok {
			if err := locker.LockForAction(ctx, building.ID(buildingID)); err != nil {
				return err
			}
		}
		return fn(ctx)
	})
}

func (s *ProductionService) Start(ctx context.Context, p player.ID, bid, recipe string) (job economy.ProductionJob, inventory economy.Inventory, err error) {
	err = s.transaction(ctx, bid, func(ctx context.Context) error {
		var e error
		job, inventory, e = s.start(ctx, p, bid, recipe)
		return e
	})
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	return
}

func (s *ProductionService) CompleteAt(ctx context.Context, p player.ID, id economy.ProductionJobID, now time.Time) (job economy.ProductionJob, inventory economy.Inventory, err error) {
	initial, e := s.repo.FindProductionJob(ctx, id)
	if e != nil {
		return job, inventory, e
	}
	err = s.transaction(ctx, initial.BuildingID, func(ctx context.Context) error {
		var e error
		job, inventory, e = s.completeAt(ctx, p, id, now)
		return e
	})
	if err != nil {
		return economy.ProductionJob{}, economy.Inventory{}, err
	}
	return
}

func (s *ProductionService) ReadyAt(ctx context.Context, p player.ID, id economy.ProductionJobID, now time.Time) (job economy.ProductionJob, err error) {
	initial, e := s.repo.FindProductionJob(ctx, id)
	if e != nil {
		return job, e
	}
	err = s.transaction(ctx, initial.BuildingID, func(ctx context.Context) error { var e error; job, e = s.readyAt(ctx, p, id, now); return e })
	return
}

func (s *ProductionService) Cancel(ctx context.Context, p player.ID, id economy.ProductionJobID) (job economy.ProductionJob, err error) {
	initial, e := s.repo.FindProductionJob(ctx, id)
	if e != nil {
		return job, e
	}
	err = s.transaction(ctx, initial.BuildingID, func(ctx context.Context) error { var e error; job, e = s.cancel(ctx, p, id); return e })
	return
}
