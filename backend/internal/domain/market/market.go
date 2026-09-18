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
	ID        OrderID
	PlayerID  player.ID
	Side      Side
	Resource  economy.ResourceType
	Amount    int
	Price     int
	Fee       int
	Status    Status
	CreatedAt time.Time
	UpdatedAt time.Time
}

func Fee(price int) int {
	fee := price / 20
	if fee < 1 {
		return 1
	}
	return fee
}
