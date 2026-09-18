package middleware

import (
	"bytes"
	"context"
	"net/http"
	"sync"
	"time"

	"real-city/backend/pkg/apperror"
)

type IdempotencyStore interface {
	Get(ctx context.Context, key string) (IdempotencyRecord, bool, error)
	Save(ctx context.Context, key string, record IdempotencyRecord, ttl time.Duration) error
}

type IdempotencyRecord struct {
	Status int
	Header http.Header
	Body   []byte
}

func Idempotency(store IdempotencyStore, ttl time.Duration) Middleware {
	if store == nil {
		store = NewMemoryIdempotencyStore(time.Now)
	}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !requiresIdempotency(r) {
				next.ServeHTTP(w, r)
				return
			}
			key := r.Header.Get("Idempotency-Key")
			if key == "" {
				writeMiddlewareError(w, http.StatusBadRequest, apperror.New(apperror.Validation, "Idempotency-Key header is required"))
				return
			}
			cacheKey := r.Header.Get("Authorization") + ":" + r.Method + ":" + r.URL.Path + ":" + key
			if record, ok, err := store.Get(r.Context(), cacheKey); err != nil {
				writeMiddlewareError(w, http.StatusInternalServerError, apperror.New(apperror.Internal, "idempotency store unavailable"))
				return
			} else if ok {
				copyHeaders(w.Header(), record.Header)
				w.Header().Set("Idempotency-Replayed", "true")
				w.WriteHeader(record.Status)
				_, _ = w.Write(record.Body)
				return
			}
			recorder := &bufferedResponse{ResponseWriter: w, status: http.StatusOK, header: make(http.Header)}
			next.ServeHTTP(recorder, r)
			copyHeaders(w.Header(), recorder.header)
			w.WriteHeader(recorder.status)
			_, _ = w.Write(recorder.body.Bytes())
			if recorder.status >= 200 && recorder.status < 300 {
				_ = store.Save(r.Context(), cacheKey, IdempotencyRecord{Status: recorder.status, Header: recorder.header.Clone(), Body: recorder.body.Bytes()}, ttl)
			}
		})
	}
}

type MemoryIdempotencyStore struct {
	mu      sync.RWMutex
	now     func() time.Time
	records map[string]memoryIdempotencyRecord
}

type memoryIdempotencyRecord struct {
	record  IdempotencyRecord
	expires time.Time
}

func NewMemoryIdempotencyStore(now func() time.Time) *MemoryIdempotencyStore {
	return &MemoryIdempotencyStore{now: now, records: make(map[string]memoryIdempotencyRecord)}
}

func (s *MemoryIdempotencyStore) Get(ctx context.Context, key string) (IdempotencyRecord, bool, error) {
	_ = ctx
	s.mu.RLock()
	item, ok := s.records[key]
	s.mu.RUnlock()
	if !ok || !item.expires.After(s.now()) {
		return IdempotencyRecord{}, false, nil
	}
	return item.record, true, nil
}

func (s *MemoryIdempotencyStore) Save(ctx context.Context, key string, record IdempotencyRecord, ttl time.Duration) error {
	_ = ctx
	s.mu.Lock()
	defer s.mu.Unlock()
	s.records[key] = memoryIdempotencyRecord{record: record, expires: s.now().Add(ttl)}
	return nil
}

type bufferedResponse struct {
	http.ResponseWriter
	status int
	header http.Header
	body   bytes.Buffer
}

func (r *bufferedResponse) Header() http.Header {
	return r.header
}

func (r *bufferedResponse) WriteHeader(status int) {
	r.status = status
}

func (r *bufferedResponse) Write(data []byte) (int, error) {
	return r.body.Write(data)
}

func requiresIdempotency(r *http.Request) bool {
	if r.Method != http.MethodPost {
		return false
	}
	switch r.URL.Path {
	case "/api/v1/buildings", "/api/v1/market/orders", "/api/v1/alliances/invites":
		return true
	default:
		return false
	}
}

func copyHeaders(dst, src http.Header) {
	for key, values := range src {
		dst.Del(key)
		for _, value := range values {
			dst.Add(key, value)
		}
	}
}
