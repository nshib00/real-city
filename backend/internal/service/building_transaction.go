package service

import (
	"context"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"time"
)

func lockBuilding(ctx context.Context, repo BuildingRepository, id building.ID) error {
	if locker, ok := repo.(interface {
		LockForAction(context.Context, building.ID) error
	}); ok {
		return locker.LockForAction(ctx, id)
	}
	return nil
}

func (s *BuildingService) buildingTransaction(ctx context.Context, id building.ID, fn func(context.Context) error) error {
	return s.DestructionTransaction(ctx, s.repairUOW, func(ctx context.Context) error {
		if err := lockBuilding(ctx, s.buildings, id); err != nil {
			return err
		}
		return fn(ctx)
	})
}

func (s *BuildingService) Place(ctx context.Context, input PlaceBuildingInput) (item building.Building, err error) {
	err = s.DestructionTransaction(ctx, s.repairUOW, func(ctx context.Context) error {
		if locker, ok := s.buildings.(interface{ LockPlacement(context.Context) error }); ok {
			if err := locker.LockPlacement(ctx); err != nil {
				return err
			}
		}
		var e error
		item, e = s.place(ctx, input)
		return e
	}, s.worlds)
	if err != nil {
		return building.Building{}, err
	}
	if waker, ok := s.monsters.(MonsterAwakener); ok {
		if wakeErr := waker.WakeNearBuilding(ctx, item.MapID, item.Tile, item.Footprint, item.CreatedAt); wakeErr != nil {
			s.log.Warn("monster.wake_near_building.failed", "building_id", item.ID, "error", wakeErr)
		}
	}
	return
}

func (s *BuildingService) UpgradeTo(ctx context.Context, id building.ID, p player.ID, target building.Type) (item building.Building, err error) {
	err = s.buildingTransaction(ctx, id, func(ctx context.Context) error { var e error; item, e = s.upgradeTo(ctx, id, p, target); return e })
	if err != nil {
		return building.Building{}, err
	}
	return
}
func (s *BuildingService) CompleteAt(ctx context.Context, id building.ID, p player.ID, now time.Time) (item building.Building, err error) {
	err = s.buildingTransaction(ctx, id, func(ctx context.Context) error { var e error; item, e = s.completeAt(ctx, id, p, now); return e })
	if err != nil {
		return building.Building{}, err
	}
	return
}
func (s *BuildingService) Demolish(ctx context.Context, id building.ID, p player.ID) error {
	return s.buildingTransaction(ctx, id, func(ctx context.Context) error { return s.demolish(ctx, id, p) })
}
func (s *BuildingService) Cancel(ctx context.Context, id building.ID, p player.ID) error {
	return s.buildingTransaction(ctx, id, func(ctx context.Context) error { return s.cancel(ctx, id, p) })
}
func (s *BuildingService) Relocate(ctx context.Context, id building.ID, p player.ID, tile world.Coord, rotation int) (item building.Building, err error) {
	err = s.buildingTransaction(ctx, id, func(ctx context.Context) error {
		if locker, ok := s.buildings.(interface{ LockPlacement(context.Context) error }); ok {
			if err := locker.LockPlacement(ctx); err != nil {
				return err
			}
		}
		var e error
		item, e = s.relocate(ctx, id, p, tile, rotation)
		return e
	})
	if err != nil {
		return building.Building{}, err
	}
	return
}
func (s *BuildingService) SetCannonEnabled(ctx context.Context, id building.ID, p player.ID, enabled bool) (item building.Building, err error) {
	err = s.buildingTransaction(ctx, id, func(ctx context.Context) error {
		var e error
		item, e = s.setCannonEnabled(ctx, id, p, enabled)
		return e
	})
	if err != nil {
		return building.Building{}, err
	}
	return
}
func (s *BuildingService) SetTowerWatchkeeper(ctx context.Context, id building.ID, p player.ID, assigned bool) (item building.Building, err error) {
	err = s.buildingTransaction(ctx, id, func(ctx context.Context) error {
		var e error
		item, e = s.setTowerWatchkeeper(ctx, id, p, assigned)
		return e
	})
	if err != nil {
		return building.Building{}, err
	}
	return
}
func (s *BuildingService) ReloadTrap(ctx context.Context, id building.ID, p player.ID) (item building.Building, err error) {
	err = s.buildingTransaction(ctx, id, func(ctx context.Context) error { var e error; item, e = s.reloadTrap(ctx, id, p); return e })
	if err != nil {
		return building.Building{}, err
	}
	return
}
func (s *BuildingService) RushComplete(ctx context.Context, id building.ID, p player.ID) (item building.Building, inv economy.Inventory, price int, err error) {
	err = s.buildingTransaction(ctx, id, func(ctx context.Context) error {
		var e error
		item, inv, price, e = s.rushComplete(ctx, id, p)
		return e
	})
	if err != nil {
		return building.Building{}, economy.Inventory{}, 0, err
	}
	return
}
