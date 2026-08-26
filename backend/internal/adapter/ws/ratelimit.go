package ws

import (
	"sync"
	"time"
)

type RateLimiter struct {
	mu       sync.Mutex
	limit    int
	window   time.Duration
	resetAt  time.Time
	consumed int
}

func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
	if limit <= 0 {
		limit = 20
	}
	if window <= 0 {
		window = time.Second
	}
	return &RateLimiter{limit: limit, window: window}
}

func (r *RateLimiter) Allow(now time.Time) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.resetAt.IsZero() || !now.Before(r.resetAt) {
		r.resetAt = now.Add(r.window)
		r.consumed = 0
	}
	if r.consumed >= r.limit {
		return false
	}
	r.consumed++
	return true
}
