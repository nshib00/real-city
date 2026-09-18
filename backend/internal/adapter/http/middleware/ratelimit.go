package middleware

import (
	"net"
	"net/http"
	"strings"
	"sync"
	"time"

	"real-city/backend/pkg/apperror"
)

type RateLimitRule struct {
	Method string
	Prefix string
	Limit  int
	Window time.Duration
}

func DefaultRateLimitRules() []RateLimitRule {
	return []RateLimitRule{
		{Method: http.MethodPost, Prefix: "/api/v1/auth/", Limit: 12, Window: time.Minute},
		{Method: http.MethodPost, Prefix: "/api/v1/buildings", Limit: 30, Window: time.Minute},
		{Method: http.MethodPost, Prefix: "/api/v1/monsters/", Limit: 45, Window: time.Minute},
		{Method: http.MethodPost, Prefix: "/api/v1/chat/", Limit: 40, Window: time.Minute},
		{Method: http.MethodPost, Prefix: "/api/v1/market/", Limit: 30, Window: time.Minute},
		{Method: http.MethodPost, Prefix: "/api/v1/alliances/", Limit: 30, Window: time.Minute},
	}
}

func RateLimit(limiter *MemoryRateLimiter, rules []RateLimitRule) Middleware {
	if limiter == nil {
		limiter = NewMemoryRateLimiter(time.Now)
	}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			rule, ok := matchingRule(r, rules)
			if !ok {
				next.ServeHTTP(w, r)
				return
			}
			key := clientIP(r) + ":" + rule.Method + ":" + rule.Prefix
			if !limiter.Allow(key, rule.Limit, rule.Window) {
				writeMiddlewareError(w, http.StatusTooManyRequests, apperror.New(apperror.RateLimited, "too many requests"))
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

type MemoryRateLimiter struct {
	mu      sync.Mutex
	now     func() time.Time
	buckets map[string]rateBucket
}

type rateBucket struct {
	resetAt time.Time
	count   int
}

func NewMemoryRateLimiter(now func() time.Time) *MemoryRateLimiter {
	return &MemoryRateLimiter{now: now, buckets: make(map[string]rateBucket)}
}

func (l *MemoryRateLimiter) Allow(key string, limit int, window time.Duration) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	now := l.now()
	bucket := l.buckets[key]
	if bucket.resetAt.IsZero() || !bucket.resetAt.After(now) {
		bucket = rateBucket{resetAt: now.Add(window)}
	}
	bucket.count++
	l.buckets[key] = bucket
	return bucket.count <= limit
}

func matchingRule(r *http.Request, rules []RateLimitRule) (RateLimitRule, bool) {
	for _, rule := range rules {
		if rule.Method == r.Method && strings.HasPrefix(r.URL.Path, rule.Prefix) {
			return rule, true
		}
	}
	return RateLimitRule{}, false
}

func clientIP(r *http.Request) string {
	if forwarded := strings.TrimSpace(r.Header.Get("X-Forwarded-For")); forwarded != "" {
		if index := strings.Index(forwarded, ","); index >= 0 {
			return strings.TrimSpace(forwarded[:index])
		}
		return forwarded
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}
