package redis

import (
	"context"
	"net/http"
	"sync"
	"time"

	httpmiddleware "real-city/backend/internal/adapter/http/middleware"
)

const NamespaceIdempotency = "idempotency"

type IdempotencyStore struct {
	mu      sync.RWMutex
	now     func() time.Time
	records map[string]idempotencyRecord
}

type idempotencyRecord struct {
	record  httpmiddleware.IdempotencyRecord
	expires time.Time
}

func NewIdempotencyStore() *IdempotencyStore {
	return &IdempotencyStore{now: func() time.Time { return time.Now().UTC() }, records: make(map[string]idempotencyRecord)}
}

func (s *IdempotencyStore) Get(ctx context.Context, key string) (httpmiddleware.IdempotencyRecord, bool, error) {
	_ = ctx
	s.mu.RLock()
	item, ok := s.records[key]
	s.mu.RUnlock()
	if !ok || !item.expires.After(s.now()) {
		return httpmiddleware.IdempotencyRecord{}, false, nil
	}
	return cloneRecord(item.record), true, nil
}

func (s *IdempotencyStore) Save(ctx context.Context, key string, record httpmiddleware.IdempotencyRecord, ttl time.Duration) error {
	_ = ctx
	s.mu.Lock()
	defer s.mu.Unlock()
	s.records[key] = idempotencyRecord{record: cloneRecord(record), expires: s.now().Add(ttl)}
	return nil
}

func cloneRecord(record httpmiddleware.IdempotencyRecord) httpmiddleware.IdempotencyRecord {
	return httpmiddleware.IdempotencyRecord{
		Status: record.Status,
		Header: record.Header.Clone(),
		Body:   append([]byte(nil), record.Body...),
	}
}

var _ interface {
	Get(context.Context, string) (httpmiddleware.IdempotencyRecord, bool, error)
	Save(context.Context, string, httpmiddleware.IdempotencyRecord, time.Duration) error
} = (*IdempotencyStore)(nil)

var _ = http.Header{}
