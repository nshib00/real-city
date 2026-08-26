package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type SessionRepo struct {
	db *sql.DB
}

func NewSessionRepo(db *sql.DB) *SessionRepo {
	return &SessionRepo{db: db}
}

func (r *SessionRepo) Save(ctx context.Context, session player.Session) error {
	revokedAt := sql.NullTime{}
	if !session.RevokedAt.IsZero() {
		revokedAt = sql.NullTime{Time: session.RevokedAt, Valid: true}
	}
	_, err := r.db.ExecContext(ctx, `
		INSERT INTO player_sessions (
			id, player_id, refresh_token_hash, user_agent, ip, expires_at,
			revoked_at, created_at, updated_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`, session.ID, session.PlayerID, session.RefreshTokenHash, session.UserAgent, session.IP,
		session.ExpiresAt, revokedAt, session.CreatedAt, session.UpdatedAt)
	return err
}

func (r *SessionRepo) FindByRefreshTokenHash(ctx context.Context, tokenHash string) (player.Session, error) {
	row := r.db.QueryRowContext(ctx, `
		SELECT id, player_id, refresh_token_hash, user_agent, ip, expires_at,
			COALESCE(revoked_at, '0001-01-01 00:00:00+00'::timestamptz), created_at, updated_at
		FROM player_sessions
		WHERE refresh_token_hash = $1
	`, tokenHash)
	var session player.Session
	err := row.Scan(&session.ID, &session.PlayerID, &session.RefreshTokenHash, &session.UserAgent,
		&session.IP, &session.ExpiresAt, &session.RevokedAt, &session.CreatedAt, &session.UpdatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return player.Session{}, apperror.New(apperror.Unauthorized, "invalid refresh token")
	}
	return session, err
}

func (r *SessionRepo) Revoke(ctx context.Context, sessionID player.SessionID) error {
	_, err := r.db.ExecContext(ctx, `UPDATE player_sessions SET revoked_at = $2, updated_at = $2 WHERE id = $1 AND revoked_at IS NULL`, sessionID, time.Now().UTC())
	return err
}

func (r *SessionRepo) RevokePlayer(ctx context.Context, playerID player.ID) error {
	_, err := r.db.ExecContext(ctx, `UPDATE player_sessions SET revoked_at = $2, updated_at = $2 WHERE player_id = $1 AND revoked_at IS NULL`, playerID, time.Now().UTC())
	return err
}
