package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestRequestIDAndCORS(t *testing.T) {
	handler := Chain(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if RequestIDFromContext(r.Context()) != "req-1" {
			t.Fatalf("request id was not stored in context")
		}
		w.WriteHeader(http.StatusOK)
	}), RequestID(), CORS([]string{"*"}))

	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	req.Header.Set("X-Request-ID", "req-1")
	req.Header.Set("Origin", "http://localhost:5173")
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d", rec.Code)
	}
	if rec.Header().Get("X-Request-ID") != "req-1" {
		t.Fatalf("missing response request id")
	}
	if rec.Header().Get("Access-Control-Allow-Origin") != "*" {
		t.Fatalf("missing CORS header")
	}
}

func TestRateLimit(t *testing.T) {
	now := time.Date(2026, 8, 29, 0, 0, 0, 0, time.UTC)
	limiter := NewMemoryRateLimiter(func() time.Time { return now })
	handler := Chain(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}), RateLimit(limiter, []RateLimitRule{{Method: http.MethodPost, Prefix: "/api/v1/chat/", Limit: 1, Window: time.Minute}}))

	first := httptest.NewRecorder()
	handler.ServeHTTP(first, httptest.NewRequest(http.MethodPost, "/api/v1/chat/messages", nil))
	if first.Code != http.StatusOK {
		t.Fatalf("first status = %d", first.Code)
	}
	second := httptest.NewRecorder()
	handler.ServeHTTP(second, httptest.NewRequest(http.MethodPost, "/api/v1/chat/messages", nil))
	if second.Code != http.StatusTooManyRequests {
		t.Fatalf("second status = %d", second.Code)
	}
}

func TestIdempotencyReplaysSuccessfulResponse(t *testing.T) {
	calls := 0
	handler := Chain(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"ok":true}`))
	}), Idempotency(NewMemoryIdempotencyStore(time.Now), time.Hour))

	req := httptest.NewRequest(http.MethodPost, "/api/v1/market/orders", nil)
	req.Header.Set("Idempotency-Key", "market-order-1")
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)
	if rec.Code != http.StatusCreated {
		t.Fatalf("first status = %d", rec.Code)
	}

	req = httptest.NewRequest(http.MethodPost, "/api/v1/market/orders", nil)
	req.Header.Set("Idempotency-Key", "market-order-1")
	rec = httptest.NewRecorder()
	handler.ServeHTTP(rec, req)
	if rec.Code != http.StatusCreated {
		t.Fatalf("replay status = %d", rec.Code)
	}
	if rec.Header().Get("Idempotency-Replayed") != "true" {
		t.Fatalf("missing replay header")
	}
	if calls != 1 {
		t.Fatalf("handler calls = %d", calls)
	}
}
