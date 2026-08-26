package service

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"log/slog"
	"strings"
	"time"

	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type AuthService struct {
	players  PlayerRepository
	sessions SessionStore
	tokens   *jwtadapter.Manager
	log      *slog.Logger
	now      func() time.Time
}

type RegisterInput struct {
	Email     string
	Name      string
	Password  string
	UserAgent string
	IP        string
}

type LoginInput struct {
	Email     string
	Password  string
	UserAgent string
	IP        string
}

type AuthResult struct {
	Player       player.Player
	AccessToken  string
	RefreshToken string
	AccessUntil  time.Time
	RefreshUntil time.Time
}

func NewAuthService(players PlayerRepository, sessions SessionStore, tokens *jwtadapter.Manager, log *slog.Logger) *AuthService {
	return &AuthService{players: players, sessions: sessions, tokens: tokens, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *AuthService) Register(ctx context.Context, input RegisterInput) (AuthResult, error) {
	email := player.NormalizeEmail(input.Email)
	name := strings.TrimSpace(input.Name)
	if err := player.ValidateEmail(email); err != nil {
		return AuthResult{}, err
	}
	if err := player.ValidateName(name); err != nil {
		return AuthResult{}, err
	}
	hash, err := player.HashPassword(input.Password)
	if err != nil {
		return AuthResult{}, err
	}
	now := s.now()
	p := player.Player{
		ID:           player.ID(newID("player")),
		Email:        email,
		Name:         name,
		PasswordHash: hash,
		Status:       player.StatusActive,
		Role:         player.RoleUser,
		Profile:      player.DefaultProfile(name, now),
		CreatedAt:    now,
		UpdatedAt:    now,
	}
	if err := s.players.Create(ctx, p); err != nil {
		return AuthResult{}, err
	}
	result, err := s.createSession(ctx, p, input.UserAgent, input.IP)
	if err != nil {
		return AuthResult{}, err
	}
	s.log.Info("auth.registered", "event", "auth.registered", "player_id", p.ID)
	return result, nil
}

func (s *AuthService) Login(ctx context.Context, input LoginInput) (AuthResult, error) {
	p, err := s.players.FindByEmail(ctx, input.Email)
	if err != nil {
		s.log.Warn("auth.login_failed", "event", "auth.login_failed", "reason", "player_not_found")
		return AuthResult{}, apperror.New(apperror.Unauthorized, "invalid email or password")
	}
	if p.Status != player.StatusActive {
		return AuthResult{}, apperror.New(apperror.Forbidden, "player is not active")
	}
	if err := player.ComparePassword(p.PasswordHash, input.Password); err != nil {
		s.log.Warn("auth.login_failed", "event", "auth.login_failed", "player_id", p.ID, "reason", "password")
		return AuthResult{}, err
	}
	result, err := s.createSession(ctx, p, input.UserAgent, input.IP)
	if err != nil {
		return AuthResult{}, err
	}
	s.log.Info("auth.login", "event", "auth.login", "player_id", p.ID)
	return result, nil
}

func (s *AuthService) Refresh(ctx context.Context, refreshToken string, userAgent string, ip string) (AuthResult, error) {
	if refreshToken == "" {
		return AuthResult{}, apperror.New(apperror.Unauthorized, "refresh token is required")
	}
	tokenHash := s.tokens.HashRefreshToken(refreshToken)
	oldSession, err := s.sessions.FindByRefreshTokenHash(ctx, tokenHash)
	if err != nil {
		s.log.Warn("auth.refresh_failed", "event", "auth.refresh_failed", "reason", "refresh_token")
		return AuthResult{}, err
	}
	if err := s.sessions.Revoke(ctx, oldSession.ID); err != nil {
		return AuthResult{}, err
	}
	p, err := s.players.FindByID(ctx, oldSession.PlayerID)
	if err != nil {
		return AuthResult{}, err
	}
	result, err := s.createSession(ctx, p, userAgent, ip)
	if err != nil {
		return AuthResult{}, err
	}
	s.log.Info("auth.refresh", "event", "auth.refresh", "player_id", p.ID)
	return result, nil
}

func (s *AuthService) Logout(ctx context.Context, refreshToken string) error {
	if refreshToken == "" {
		return nil
	}
	session, err := s.sessions.FindByRefreshTokenHash(ctx, s.tokens.HashRefreshToken(refreshToken))
	if err != nil {
		return nil
	}
	if err := s.sessions.Revoke(ctx, session.ID); err != nil {
		return err
	}
	s.log.Info("auth.logout", "event", "auth.logout", "player_id", session.PlayerID, "session_id", session.ID)
	return nil
}

func (s *AuthService) LogoutAll(ctx context.Context, playerID player.ID) error {
	if err := s.sessions.RevokePlayer(ctx, playerID); err != nil {
		return err
	}
	s.log.Info("auth.logout_all", "event", "auth.logout_all", "player_id", playerID)
	return nil
}

func (s *AuthService) createSession(ctx context.Context, p player.Player, userAgent string, ip string) (AuthResult, error) {
	now := s.now()
	sessionID := player.SessionID(newID("session"))
	pair, err := s.tokens.Issue(p.ID, sessionID, now)
	if err != nil {
		return AuthResult{}, err
	}
	session := player.Session{
		ID:               sessionID,
		PlayerID:         p.ID,
		RefreshTokenHash: s.tokens.HashRefreshToken(pair.RefreshToken),
		UserAgent:        truncate(userAgent, 512),
		IP:               truncate(ip, 128),
		ExpiresAt:        pair.RefreshUntil,
		CreatedAt:        now,
		UpdatedAt:        now,
	}
	if err := s.sessions.Save(ctx, session); err != nil {
		return AuthResult{}, err
	}
	return AuthResult{Player: p, AccessToken: pair.AccessToken, RefreshToken: pair.RefreshToken, AccessUntil: pair.AccessUntil, RefreshUntil: pair.RefreshUntil}, nil
}

func newID(prefix string) string {
	raw := make([]byte, 16)
	if _, err := rand.Read(raw); err != nil {
		return prefix + "_fallback"
	}
	return prefix + "_" + hex.EncodeToString(raw)
}

func truncate(value string, max int) string {
	if len(value) <= max {
		return value
	}
	return value[:max]
}
