// Package memorytx coordinates the in-memory adapters during snapshot transactions.
package memorytx

import (
	"context"
	"sync"
)

type key struct{}

var gate sync.RWMutex

// Guard permits concurrent ordinary calls, but excludes snapshot transactions.
// A derived context avoids reacquiring the gate during nested repository calls.
func Guard(ctx context.Context) (context.Context, func()) {
	if ctx.Value(key{}) != nil {
		return ctx, func() {}
	}
	gate.RLock()
	return context.WithValue(ctx, key{}, true), gate.RUnlock
}
func Begin(ctx context.Context) (context.Context, func()) {
	gate.Lock()
	return context.WithValue(ctx, key{}, true), gate.Unlock
}
