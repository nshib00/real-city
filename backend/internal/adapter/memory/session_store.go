package memory

import (
	"context"
	"sync"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
	"real-city/backend/pkg/memorytx"
)

type SessionStore struct {
	mu       sync.RWMutex
	byID     map[player.SessionID]player.Session
	byToken  map[string]player.SessionID
	byPlayer map[player.ID]map[player.SessionID]struct{}
}

func NewSessionStore() *SessionStore {
	return &SessionStore{
		byID:     make(map[player.SessionID]player.Session),
		byToken:  make(map[string]player.SessionID),
		byPlayer: make(map[player.ID]map[player.SessionID]struct{}),
	}
}

func (s *SessionStore) Save(ctx context.Context, session player.Session) error {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	_ = ctx
	s.mu.Lock()
	defer s.mu.Unlock()
	s.byID[session.ID] = session
	s.byToken[session.RefreshTokenHash] = session.ID
	if _, ok := s.byPlayer[session.PlayerID]; !ok {
		s.byPlayer[session.PlayerID] = make(map[player.SessionID]struct{})
	}
	s.byPlayer[session.PlayerID][session.ID] = struct{}{}
	return nil
}

func (s *SessionStore) FindByRefreshTokenHash(ctx context.Context, tokenHash string) (player.Session, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	_ = ctx
	s.mu.RLock()
	defer s.mu.RUnlock()
	id, ok := s.byToken[tokenHash]
	if !ok {
		return player.Session{}, apperror.New(apperror.Unauthorized, "invalid refresh token")
	}
	session := s.byID[id]
	if !session.RevokedAt.IsZero() || time.Now().UTC().After(session.ExpiresAt) {
		return player.Session{}, apperror.New(apperror.Unauthorized, "invalid refresh token")
	}
	return session, nil
}

func (s *SessionStore) Revoke(ctx context.Context, sessionID player.SessionID) error {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	_ = ctx
	s.mu.Lock()
	defer s.mu.Unlock()
	session, ok := s.byID[sessionID]
	if !ok {
		return nil
	}
	session.RevokedAt = time.Now().UTC()
	session.UpdatedAt = session.RevokedAt
	s.byID[sessionID] = session
	return nil
}

func (s *SessionStore) RevokePlayer(ctx context.Context, playerID player.ID) error {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	_ = ctx
	s.mu.Lock()
	defer s.mu.Unlock()
	for id := range s.byPlayer[playerID] {
		session := s.byID[id]
		session.RevokedAt = time.Now().UTC()
		session.UpdatedAt = session.RevokedAt
		s.byID[id] = session
	}
	return nil
}

func (s *SessionStore) SessionActive(ctx context.Context, p player.ID, id player.SessionID, now time.Time) (bool, error) {
	ctx, release := memorytx.Guard(ctx)
	defer release()
	s.mu.RLock()
	defer s.mu.RUnlock()
	item, ok := s.byID[id]
	return ok && item.PlayerID == p && item.RevokedAt.IsZero() && item.ExpiresAt.After(now), nil
}

func (s *SessionStore) Snapshot() func() {
	s.mu.RLock()
	defer s.mu.RUnlock()
	items := make(map[player.SessionID]player.Session, len(s.byID))
	for id, item := range s.byID {
		items[id] = item
	}
	return func() { s.mu.Lock(); defer s.mu.Unlock(); s.byID = items }
}
