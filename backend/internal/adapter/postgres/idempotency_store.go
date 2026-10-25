package postgres

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"hash/fnv"
	"time"

	"real-city/backend/internal/adapter/http/middleware"
)

type IdempotencyStore struct{ db *sql.DB }

func NewIdempotencyStore(db *sql.DB) *IdempotencyStore { return &IdempotencyStore{db: db} }

// The session advisory lock keeps duplicate requests on different API processes serialized.
func (s *IdempotencyStore) Lock(ctx context.Context, key string) (func(), error) {
	conn, err := s.db.Conn(ctx)
	if err != nil {
		return nil, err
	}
	h := fnv.New64a()
	_, _ = h.Write([]byte(key))
	lockID := int64(h.Sum64())
	if _, err = conn.ExecContext(ctx, `SELECT pg_advisory_lock($1)`, lockID); err != nil {
		_ = conn.Close()
		return nil, err
	}
	return func() {
		_, _ = conn.ExecContext(context.Background(), `SELECT pg_advisory_unlock($1)`, lockID)
		_ = conn.Close()
	}, nil
}

func (s *IdempotencyStore) Get(ctx context.Context, key string) (middleware.IdempotencyRecord, bool, error) {
	var record middleware.IdempotencyRecord
	var headers []byte
	err := s.db.QueryRowContext(ctx, `SELECT status, headers, body, fingerprint FROM http_idempotency_responses WHERE key_hash=$1 AND (state='pending' OR expires_at > now())`, key).Scan(&record.Status, &headers, &record.Body, &record.Fingerprint)
	if errors.Is(err, sql.ErrNoRows) {
		return middleware.IdempotencyRecord{}, false, nil
	}
	if err != nil {
		return middleware.IdempotencyRecord{}, false, err
	}
	if err := json.Unmarshal(headers, &record.Header); err != nil {
		return middleware.IdempotencyRecord{}, false, err
	}
	return record, true, nil
}

func (s *IdempotencyStore) Save(ctx context.Context, key string, record middleware.IdempotencyRecord, ttl time.Duration) error {
	headers, err := json.Marshal(record.Header)
	if err != nil {
		return err
	}
	result, err := s.db.ExecContext(ctx, `INSERT INTO http_idempotency_responses(key_hash, fingerprint, status, headers, body, expires_at, state) VALUES ($1,$2,$3,$4,$5,$6,'completed') ON CONFLICT (key_hash) DO UPDATE SET status=EXCLUDED.status, headers=EXCLUDED.headers, body=EXCLUDED.body, expires_at=EXCLUDED.expires_at, state='completed' WHERE http_idempotency_responses.fingerprint=EXCLUDED.fingerprint AND http_idempotency_responses.state='pending'`, key, record.Fingerprint, record.Status, headers, record.Body, time.Now().Add(ttl))
	if err != nil {
		return err
	}
	count, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if count != 1 {
		return fmt.Errorf("idempotency reservation was not completed")
	}
	return nil
}

func (s *IdempotencyStore) Begin(ctx context.Context, key, fingerprint string, ttl time.Duration) (bool, error) {
	var created bool
	err := s.db.QueryRowContext(ctx, `WITH claim AS (
		INSERT INTO http_idempotency_responses(key_hash, fingerprint, status, headers, body, expires_at, state)
		VALUES ($1, $2, 0, '{}'::jsonb, ''::bytea, now()+($3 * interval '1 second'), 'pending')
		ON CONFLICT (key_hash) DO UPDATE SET fingerprint=EXCLUDED.fingerprint, status=0, headers='{}'::jsonb, body=''::bytea, expires_at=EXCLUDED.expires_at, state='pending'
		WHERE http_idempotency_responses.state='completed' AND http_idempotency_responses.expires_at <= now()
		RETURNING true
	) SELECT EXISTS(SELECT 1 FROM claim)`, key, fingerprint, int64(ttl/time.Second)).Scan(&created)
	return created, err
}

func (s *IdempotencyStore) Abort(ctx context.Context, key, fingerprint string) error {
	_, err := s.db.ExecContext(ctx, `DELETE FROM http_idempotency_responses WHERE key_hash=$1 AND fingerprint=$2 AND state='pending'`, key, fingerprint)
	return err
}

var _ middleware.IdempotencyStore = (*IdempotencyStore)(nil)
var _ middleware.IdempotencyLocker = (*IdempotencyStore)(nil)
var _ middleware.IdempotencyReservationStore = (*IdempotencyStore)(nil)
