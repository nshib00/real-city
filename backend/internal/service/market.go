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
	events  *EventBus
	uow     UnitOfWork
	economy *EconomyService
	log     *slog.Logger
	now     func() time.Time
}

func NewMarketService(repo MarketRepository, economyService *EconomyService, log *slog.Logger) *MarketService {
	return &MarketService{repo: repo, economy: economyService, uow: snapshotUnitOfWork{[]any{repo, economyService.repo}}, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *MarketService) List(ctx context.Context, limit int) ([]market.Order, error) {
	return s.repo.ListOrders(ctx, market.StatusOpen, limit)
}

func (s *MarketService) create(ctx context.Context, playerID player.ID, side market.Side, resource economy.ResourceType, amount, price int) (market.Order, error) {
	if side != market.SideBuy && side != market.SideSell {
		return market.Order{}, apperror.New(apperror.Validation, "side must be buy or sell")
	}
	if amount <= 0 || price <= 0 || amount > 2147483647 || price > 2147483647 {
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

func (s *MarketService) cancel(ctx context.Context, playerID player.ID, orderID market.OrderID) (market.Order, error) {
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
		refund = append(refund, economy.ResourceAmount{Resource: item.Resource, Amount: item.Remaining()})
	} else {
		refund = append(refund, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: item.ReservedCoins()})
	}
	if _, _, err := s.economy.Add(withUncappedCoins(ctx), playerID, refund, "market_order_cancel_refund"); err != nil {
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

func (s *MarketService) SetUnitOfWork(uow UnitOfWork) {
	if uow != nil {
		s.uow = uow
	}
}
func (s *MarketService) Create(ctx context.Context, p player.ID, side market.Side, resource economy.ResourceType, amount, price int) (item market.Order, err error) {
	valid := false
	for _, r := range economy.AllResourceTypes() {
		if r == resource {
			valid = true
			break
		}
	}
	if !valid {
		return item, apperror.New(apperror.Validation, "unknown resource")
	}
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		var e error
		if resource == economy.ResourceCoins || resource == economy.ResourcePopulation {
			return apperror.New(apperror.Validation, "Этот ресурс нельзя продавать")
		}
		if e = s.repo.LockMarket(ctx, resource); e != nil {
			return e
		}
		item, e = s.create(WithoutCatchUp(ctx), p, side, resource, amount, price)
		if e != nil {
			return e
		}
		item, e = s.match(WithoutCatchUp(ctx), item)
		if e == nil {
			s.marketEvent(ctx, item, "market.order.created")
		}
		return e
	})
	return
}
func (s *MarketService) Cancel(ctx context.Context, p player.ID, id market.OrderID) (item market.Order, err error) {
	err = transactional(ctx, s.uow, func(ctx context.Context) error {
		var e error
		existing, err := s.repo.FindOrder(ctx, id)
		if err != nil {
			return err
		}
		if e = s.repo.LockMarket(ctx, existing.Resource); e != nil {
			return e
		}
		item, e = s.cancel(WithoutCatchUp(ctx), p, id)
		if e == nil {
			s.marketEvent(ctx, item, "market.order.cancelled")
		}
		return e
	})
	return
}

func (s *MarketService) SetEventBus(events *EventBus) { s.events = events }
func (s *MarketService) marketEvent(ctx context.Context, item market.Order, kind EventType) {
	publishEvent(ctx, s.events, Event{Type: kind, PlayerID: item.PlayerID, Payload: map[string]any{"order": map[string]any{"id": item.ID, "player_id": item.PlayerID, "side": item.Side, "resource": item.Resource, "amount": item.Amount, "filled_amount": item.FilledAmount, "price": item.Price, "fee": item.Fee, "status": item.Status, "created_at": item.CreatedAt, "updated_at": item.UpdatedAt}}})
}

// Price is the TOTAL original lot price, not a per-unit price.
// Compatible portions cross at the older order's price without rounding coins.
func (s *MarketService) match(ctx context.Context, item market.Order) (market.Order, error) {
	for item.Status == market.StatusOpen {
		other, err := s.repo.FindMatch(ctx, item)
		if isNotFound(err) {
			return item, nil
		}
		if err != nil {
			return item, err
		}
		buy, sell := item, other
		if item.Side == market.SideSell {
			buy, sell = other, item
		}
		// Acquire both inventory locks in a stable order before making any transfers.
		first, second := buy.PlayerID, sell.PlayerID
		if first > second {
			first, second = second, first
		}
		if _, err = s.economy.Inventory(ctx, first); err != nil {
			return item, err
		}
		if _, err = s.economy.Inventory(ctx, second); err != nil {
			return item, err
		}
		quantity := market.TradeQuantity(buy, sell)
		if quantity == 0 {
			return item, apperror.New(apperror.Conflict, "Несовместимый размер торговой части")
		}
		executionPrice := int(int64(quantity) * int64(other.Price) / int64(other.Amount))
		if _, overflow, e := s.economy.Add(ctx, sell.PlayerID, []economy.ResourceAmount{{Resource: economy.ResourceCoins, Amount: executionPrice}}, "market:trade:"+string(item.ID)); e != nil {
			return item, e
		} else if len(overflow) > 0 {
			return item, apperror.New(apperror.Conflict, "Хранилище продавца заполнено")
		}
		refund := int(int64(quantity)*int64(buy.Price)/int64(buy.Amount)) - executionPrice
		grant := []economy.ResourceAmount{{Resource: buy.Resource, Amount: quantity}}
		if refund > 0 {
			grant = append(grant, economy.ResourceAmount{Resource: economy.ResourceCoins, Amount: refund})
		}
		if _, _, err = s.economy.Add(withUncappedCoins(ctx), buy.PlayerID, grant, "market:trade:"+string(item.ID)); err != nil {
			return item, err
		}
		item.FilledAmount += quantity
		other.FilledAmount += quantity
		if item.Remaining() == 0 {
			item.Status = market.StatusFilled
		}
		if other.Remaining() == 0 {
			other.Status = market.StatusFilled
		}
		item.UpdatedAt = s.now()
		other.UpdatedAt = item.UpdatedAt
		if err = s.repo.UpdateOrder(ctx, item); err != nil {
			return item, err
		}
		if err = s.repo.UpdateOrder(ctx, other); err != nil {
			return item, err
		}
		s.marketEvent(ctx, item, "market.order.filled")
		s.marketEvent(ctx, other, "market.order.filled")
	}
	return item, nil
}
