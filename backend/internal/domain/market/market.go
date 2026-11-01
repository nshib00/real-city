package market

import (
	"time"

	"real-city/backend/internal/domain/economy"
	"real-city/backend/internal/domain/player"
)

type OrderID string
type Side string
type Status string

const (
	SideSell Side = "sell"
	SideBuy  Side = "buy"

	StatusOpen      Status = "open"
	StatusFilled    Status = "filled"
	StatusCancelled Status = "cancelled"
)

type Order struct {
	ID           OrderID
	PlayerID     player.ID
	Side         Side
	Resource     economy.ResourceType
	Amount       int
	Price        int
	Fee          int
	Status       Status
	CreatedAt    time.Time
	UpdatedAt    time.Time
	FilledAmount int
}

func (o Order) Remaining() int { return o.Amount - o.FilledAmount }
func (o Order) ReservedCoins() int {
	return o.Price - int(int64(o.FilledAmount)*int64(o.Price)/int64(o.Amount))
}

// Price remains the total original lot price. Trade in the smallest common
// integer quantity that preserves both limit prices without rounding coins.
func TradeQuantity(a, b Order) int {
	if a.Amount <= 0 || b.Amount <= 0 || a.Price <= 0 || b.Price <= 0 {
		return 0
	}
	gcd := func(a, b int64) int64 {
		for b != 0 {
			a, b = b, a%b
		}
		return a
	}
	qa := int64(a.Amount) / gcd(int64(a.Amount), int64(a.Price))
	qb := int64(b.Amount) / gcd(int64(b.Amount), int64(b.Price))
	quantum := qa / gcd(qa, qb) * qb
	remaining := int64(min(a.Remaining(), b.Remaining()))
	if remaining < quantum {
		return 0
	}
	return int(remaining / quantum * quantum)
}

func Fee(price int) int {
	fee := price / 20
	if fee < 1 {
		return 1
	}
	return fee
}
