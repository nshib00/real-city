package market

import "testing"

func TestTradeQuantityPreservesIntegerPrices(t *testing.T) {
	for _, tc := range []struct {
		a, b Order
		want int
	}{
		{Order{Amount: 100, Price: 200}, Order{Amount: 30, Price: 90}, 30},
		{Order{Amount: 100, Price: 1}, Order{Amount: 30, Price: 1}, 0},
		{Order{Amount: 6, Price: 4}, Order{Amount: 9, Price: 6}, 6},
		{Order{Amount: 100, Price: 200, FilledAmount: 90}, Order{Amount: 30, Price: 90}, 10},
		{Order{Amount: 2147483647, Price: 2147483646}, Order{Amount: 2147483646, Price: 2147483645}, 0},
	} {
		if got := TradeQuantity(tc.a, tc.b); got != tc.want {
			t.Fatalf("TradeQuantity(%+v,%+v)=%d want %d", tc.a, tc.b, got, tc.want)
		}
	}
}
