package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

const BaseCoinCapacity = 2000

type EconomyService struct {
	repo      EconomyRepository
	buildings BuildingRepository
	log       *slog.Logger
	now       func() time.Time
}

func NewEconomyService(repo EconomyRepository, buildings BuildingRepository, log *slog.Logger) *EconomyService {
	return &EconomyService{repo: repo, buildings: buildings, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *EconomyService) Inventory(ctx context.Context, playerID player.ID) (economy.Inventory, error) {
	capacity, err := s.CoinCapacity(ctx, playerID)
	if err != nil {
		return economy.Inventory{}, err
	}
	return s.repo.GetInventory(ctx, playerID, capacity)
}

func (s *EconomyService) Spend(ctx context.Context, playerID player.ID, cost []economy.ResourceAmount, reason string) (economy.Inventory, error) {
	inventory, err := s.Inventory(ctx, playerID)
	if err != nil {
		return economy.Inventory{}, err
	}
	if !inventory.Spend(cost, s.now()) {
		s.log.Warn("economy.resource.shortage", "event", "economy.resource.shortage", "player_id", playerID, "reason", reason)
		return economy.Inventory{}, apperror.New(apperror.Conflict, "not enough resources")
	}
	if err := s.repo.SaveInventory(ctx, inventory); err != nil {
		return economy.Inventory{}, err
	}
	for _, item := range cost {
		_ = s.logTransaction(ctx, playerID, economy.TransactionSpend, item, reason)
	}
	return inventory, nil
}

func (s *EconomyService) Add(ctx context.Context, playerID player.ID, items []economy.ResourceAmount, reason string) (economy.Inventory, []economy.ResourceAmount, error) {
	inventory, err := s.Inventory(ctx, playerID)
	if err != nil {
		return economy.Inventory{}, nil, err
	}
	overflow := inventory.Add(items, s.now())
	if err := s.repo.SaveInventory(ctx, inventory); err != nil {
		return economy.Inventory{}, nil, err
	}
	for _, item := range items {
		_ = s.logTransaction(ctx, playerID, economy.TransactionAdd, item, reason)
	}
	for _, item := range overflow {
		s.log.Warn("economy.coin_capacity.overflow", "event", "economy.coin_capacity.overflow", "player_id", playerID, "overflow", item.Amount)
	}
	return inventory, overflow, nil
}

func (s *EconomyService) Transactions(ctx context.Context, playerID player.ID, limit int) ([]economy.Transaction, error) {
	return s.repo.ListTransactions(ctx, playerID, limit)
}

func (s *EconomyService) CoinCapacity(ctx context.Context, playerID player.ID) (int, error) {
	if s.buildings == nil {
		return BaseCoinCapacity, nil
	}
	buildings, err := s.buildings.ListByPlayer(ctx, playerID)
	if err != nil {
		return 0, err
	}
	capacity := BaseCoinCapacity
	for _, item := range buildings {
		if item.Type == building.TypeCoinStorage {
			capacity += 1500 * max(1, item.Level)
		}
	}
	return capacity, nil
}

func (s *EconomyService) logTransaction(ctx context.Context, playerID player.ID, kind economy.TransactionKind, item economy.ResourceAmount, reason string) error {
	tx := economy.Transaction{
		ID:        economy.TransactionID(fmt.Sprintf("tx_%d_%s", s.now().UnixNano(), item.Resource)),
		PlayerID:  string(playerID),
		Kind:      kind,
		Resource:  item.Resource,
		Amount:    item.Amount,
		Reason:    reason,
		CreatedAt: s.now(),
	}
	s.log.Info("economy.resource.changed", "event", "economy.resource.changed", "player_id", playerID, "kind", kind, "resource", item.Resource, "amount", item.Amount, "reason", reason)
	return s.repo.AddTransaction(ctx, tx)
}
