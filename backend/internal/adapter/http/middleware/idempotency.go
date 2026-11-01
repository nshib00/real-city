package middleware

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"

	"real-city/backend/pkg/apperror"
)

type IdempotencyStore interface {
	Get(ctx context.Context, key string) (IdempotencyRecord, bool, error)
	Save(ctx context.Context, key string, record IdempotencyRecord, ttl time.Duration) error
}

type IdempotencyRecord struct {
	Status      int
	Header      http.Header
	Body        []byte
	Fingerprint string
}

// IdempotencyLocker serializes requests with the same key across application instances.
type IdempotencyLocker interface {
	Lock(context.Context, string) (func(), error)
}

// A pending reservation survives a process crash and prevents a second execution.
type IdempotencyReservationStore interface {
	Begin(context.Context, string, string, time.Duration) (bool, error)
	Abort(context.Context, string, string) error
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
			if len(key) < 8 || len(key) > 128 {
				writeMiddlewareError(w, http.StatusBadRequest, apperror.New(apperror.Validation, "Idempotency-Key must contain 8 to 128 characters"))
				return
			}
			body, err := io.ReadAll(r.Body)
			if err != nil {
				writeMiddlewareError(w, http.StatusBadRequest, apperror.New(apperror.Validation, "request body is unreadable"))
				return
			}
			r.Body = io.NopCloser(bytes.NewReader(body))
			actor := r.Header.Get("Authorization")
			if playerID, ok := PlayerID(r.Context()); ok {
				actor = string(playerID)
			}
			identity := sha256.Sum256([]byte(actor + "\x00" + r.Method + "\x00" + r.URL.Path + "\x00" + key))
			cacheKey := hex.EncodeToString(identity[:])
			requestHash := sha256.Sum256(body)
			fingerprint := hex.EncodeToString(requestHash[:])
			if locker, ok := store.(IdempotencyLocker); ok {
				unlock, err := locker.Lock(r.Context(), cacheKey)
				if err != nil {
					writeMiddlewareError(w, http.StatusInternalServerError, apperror.New(apperror.Internal, "idempotency store unavailable"))
					return
				}
				defer unlock()
			}
			if record, ok, err := store.Get(r.Context(), cacheKey); err != nil {
				writeMiddlewareError(w, http.StatusInternalServerError, apperror.New(apperror.Internal, "idempotency store unavailable"))
				return
			} else if ok {
				if record.Fingerprint != fingerprint {
					writeMiddlewareError(w, http.StatusConflict, apperror.New(apperror.Conflict, "Idempotency-Key was used with another request body"))
					return
				}
				if record.Status == 0 {
					writeMiddlewareError(w, http.StatusConflict, apperror.New(apperror.Conflict, "request is pending reconciliation"))
					return
				}
				copyHeaders(w.Header(), record.Header)
				w.Header().Set("Idempotency-Replayed", "true")
				w.WriteHeader(record.Status)
				_, _ = w.Write(record.Body)
				return
			}
			reservation, hasReservation := store.(IdempotencyReservationStore)
			if hasReservation {
				created, err := reservation.Begin(r.Context(), cacheKey, fingerprint, ttl)
				if err != nil {
					writeMiddlewareError(w, http.StatusInternalServerError, apperror.New(apperror.Internal, "idempotency store unavailable"))
					return
				}
				if !created {
					writeMiddlewareError(w, http.StatusConflict, apperror.New(apperror.Conflict, "request is pending reconciliation"))
					return
				}
			}
			recorder := &bufferedResponse{ResponseWriter: w, status: http.StatusOK, header: make(http.Header)}
			next.ServeHTTP(recorder, r)
			if recorder.status >= 200 && recorder.status < 300 {
				if err := store.Save(r.Context(), cacheKey, IdempotencyRecord{Status: recorder.status, Header: recorder.header.Clone(), Body: recorder.body.Bytes(), Fingerprint: fingerprint}, ttl); err != nil {
					writeMiddlewareError(w, http.StatusInternalServerError, apperror.New(apperror.Internal, "idempotency store unavailable"))
					return
				}
			} else if hasReservation {
				if err := reservation.Abort(r.Context(), cacheKey, fingerprint); err != nil {
					writeMiddlewareError(w, http.StatusInternalServerError, apperror.New(apperror.Internal, "idempotency store unavailable"))
					return
				}
			}
			copyHeaders(w.Header(), recorder.header)
			w.WriteHeader(recorder.status)
			_, _ = w.Write(recorder.body.Bytes())
		})
	}
}

type MemoryIdempotencyStore struct {
	mu        sync.RWMutex
	requestMu sync.Mutex
	now       func() time.Time
	records   map[string]memoryIdempotencyRecord
}

func (s *MemoryIdempotencyStore) Lock(ctx context.Context, key string) (func(), error) {
	_ = ctx
	_ = key
	s.requestMu.Lock()
	return s.requestMu.Unlock, nil
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
	if !ok || (item.record.Status != 0 && !item.expires.After(s.now())) {
		return IdempotencyRecord{}, false, nil
	}
	return item.record, true, nil
}

func (s *MemoryIdempotencyStore) Begin(ctx context.Context, key, fingerprint string, ttl time.Duration) (bool, error) {
	_ = ctx
	s.mu.Lock()
	defer s.mu.Unlock()
	if item, ok := s.records[key]; ok && (item.record.Status == 0 || item.expires.After(s.now())) {
		return false, nil
	}
	s.records[key] = memoryIdempotencyRecord{record: IdempotencyRecord{Fingerprint: fingerprint}, expires: s.now().Add(ttl)}
	return true, nil
}

func (s *MemoryIdempotencyStore) Abort(ctx context.Context, key, fingerprint string) error {
	_ = ctx
	s.mu.Lock()
	defer s.mu.Unlock()
	if item, ok := s.records[key]; ok && item.record.Status == 0 && item.record.Fingerprint == fingerprint {
		delete(s.records, key)
	}
	return nil
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
	case "/api/v1/buildings", "/api/v1/combat/monsters", "/api/v1/market/orders", "/api/v1/alliances/invites":
		return true
	default:
		return strings.HasPrefix(r.URL.Path, "/api/v1/buildings/") && strings.HasSuffix(r.URL.Path, "/weapons")
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
