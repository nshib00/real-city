package redis

import (
	"context"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/player"
)

type SessionStore struct {
	fallback *memory.SessionStore
}

func NewSessionStore(_ *Client) *SessionStore {
	return &SessionStore{fallback: memory.NewSessionStore()}
}

func (s *SessionStore) Save(ctx context.Context, session player.Session) error {
	return s.fallback.Save(ctx, session)
}

func (s *SessionStore) FindByRefreshTokenHash(ctx context.Context, tokenHash string) (player.Session, error) {
	return s.fallback.FindByRefreshTokenHash(ctx, tokenHash)
}

func (s *SessionStore) Revoke(ctx context.Context, sessionID player.SessionID) error {
	return s.fallback.Revoke(ctx, sessionID)
}

func (s *SessionStore) RevokePlayer(ctx context.Context, playerID player.ID) error {
	return s.fallback.RevokePlayer(ctx, playerID)
}
