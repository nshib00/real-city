package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/market"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type MarketService struct {
	repo    MarketRepository
	economy *EconomyService
	log     *slog.Logger
	now     func() time.Time
}

func NewMarketService(repo MarketRepository, economyService *EconomyService, log *slog.Logger) *MarketService {
	return &MarketService{repo: repo, economy: economyService, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *MarketService) List(ctx context.Context, limit int) ([]market.Order, error) {
	return s.repo.ListOrders(ctx, market.StatusOpen, limit)
}

func (s *MarketService) Create(ctx context.Context, playerID player.ID, side market.Side, resource economy.ResourceType, amount, price int) (market.Order, error) {
	if side != market.SideBuy && side != market.SideSell {
		return market.Order{}, apperror.New(apperror.Validation, "side must be buy or sell")
	}
	if amount <= 0 || price <= 0 {
		return market.Order{}, apperror.New(apperror.Validation, "amount and price must be positive")
	}
	fee := market.Fee(price)
	reserve := []economy.ResourceAmount{{Resource: economy.ResourceCoins, Amount: fee}}
	if side == market.SideSell {
		reserve = append(reserve, economy.ResourceAmount{Resource: resource, Amount: amount})
	} else {
		reserve = append(reserve, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: price})
	}
	if _, err := s.economy.Spend(ctx, playerID, reserve, "market_order_reserve"); err != nil {
		return market.Order{}, err
	}
	now := s.now()
	item := market.Order{ID: market.OrderID(fmt.Sprintf("order_%d", now.UnixNano())), PlayerID: playerID, Side: side, Resource: resource, Amount: amount, Price: price, Fee: fee, Status: market.StatusOpen, CreatedAt: now, UpdatedAt: now}
	if err := s.repo.CreateOrder(ctx, item); err != nil {
		return market.Order{}, err
	}
	s.log.Info("market.order.created", "event", "market.order.created", "order_id", item.ID, "player_id", playerID, "side", side, "resource", resource, "amount", amount, "price", price, "fee", fee)
	return item, nil
}

func (s *MarketService) Cancel(ctx context.Context, playerID player.ID, orderID market.OrderID) (market.Order, error) {
	item, err := s.repo.FindOrder(ctx, orderID)
	if err != nil {
		return market.Order{}, err
	}
	if item.PlayerID != playerID {
		return market.Order{}, apperror.New(apperror.Forbidden, "cannot cancel another player's order")
	}
	if item.Status != market.StatusOpen {
		return market.Order{}, apperror.New(apperror.Conflict, "market order is not open")
	}
	refund := []economy.ResourceAmount{}
	if item.Side == market.SideSell {
		refund = append(refund, economy.ResourceAmount{Resource: item.Resource, Amount: item.Amount})
	} else {
		refund = append(refund, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: item.Price})
	}
	if _, _, err := s.economy.Add(ctx, playerID, refund, "market_order_cancel_refund"); err != nil {
		return market.Order{}, err
	}
	item.Status = market.StatusCancelled
	item.UpdatedAt = s.now()
	if err := s.repo.UpdateOrder(ctx, item); err != nil {
		return market.Order{}, err
	}
	s.log.Info("market.order.cancelled", "event", "market.order.cancelled", "order_id", item.ID, "player_id", playerID)
	return item, nil
}
