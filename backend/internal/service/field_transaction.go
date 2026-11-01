package service

import (
	"context"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

func (s *FieldService) fieldTransaction(ctx context.Context, id building.ID, fn func(context.Context) error) error {
	// Share the production lock and rollback boundary with harvest/destruction.
	prod := ProductionService{repo: s.economy.repo, buildings: s.buildings, experience: s.experience, uow: s.economy.uow}
	return prod.transaction(ctx, string(id), fn)
}
func (s *FieldService) HarvestField(ctx context.Context, p player.ID, id building.ID) (item building.Building, inv economy.Inventory, err error) {
	err = s.fieldTransaction(ctx, id, func(ctx context.Context) error { var e error; item, inv, e = s.harvestField(ctx, p, id); return e })
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	return
}
func (s *FieldService) AdvanceField(ctx context.Context, p player.ID, id building.ID) (item building.Building, inv economy.Inventory, err error) {
	err = s.fieldTransaction(ctx, id, func(ctx context.Context) error { var e error; item, inv, e = s.advanceField(ctx, p, id); return e })
	if err != nil {
		return building.Building{}, economy.Inventory{}, err
	}
	return
}
