package jwt

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type Manager struct {
	secret     []byte
	accessTTL  time.Duration
	refreshTTL time.Duration
}

type Claims struct {
	Subject   player.ID `json:"sub"`
	SessionID string    `json:"sid"`
	ExpiresAt int64     `json:"exp"`
	IssuedAt  int64     `json:"iat"`
	Type      string    `json:"typ"`
}

type TokenPair struct {
	AccessToken  string
	RefreshToken string
	AccessUntil  time.Time
	RefreshUntil time.Time
}

func NewManager(secret string, accessTTL time.Duration, refreshTTL time.Duration) *Manager {
	return &Manager{secret: []byte(secret), accessTTL: accessTTL, refreshTTL: refreshTTL}
}

func (m *Manager) Issue(playerID player.ID, sessionID player.SessionID, now time.Time) (TokenPair, error) {
	accessUntil := now.Add(m.accessTTL)
	refreshUntil := now.Add(m.refreshTTL)
	refreshToken, err := randomToken(32)
	if err != nil {
		return TokenPair{}, err
	}
	accessToken, err := m.sign(Claims{
		Subject:   playerID,
		SessionID: string(sessionID),
		ExpiresAt: accessUntil.Unix(),
		IssuedAt:  now.Unix(),
		Type:      "access",
	})
	if err != nil {
		return TokenPair{}, err
	}
	return TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		AccessUntil:  accessUntil,
		RefreshUntil: refreshUntil,
	}, nil
}

func (m *Manager) VerifyAccess(token string, now time.Time) (Claims, error) {
	claims, err := m.verify(token)
	if err != nil {
		return Claims{}, err
	}
	if claims.Type != "access" {
		return Claims{}, apperror.New(apperror.Unauthorized, "invalid access token")
	}
	if now.Unix() >= claims.ExpiresAt {
		return Claims{}, apperror.New(apperror.Unauthorized, "access token expired")
	}
	return claims, nil
}

func (m *Manager) HashRefreshToken(token string) string {
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:])
}

func (m *Manager) sign(claims Claims) (string, error) {
	header := map[string]string{"alg": "HS256", "typ": "JWT"}
	headerJSON, err := json.Marshal(header)
	if err != nil {
		return "", err
	}
	claimsJSON, err := json.Marshal(claims)
	if err != nil {
		return "", err
	}
	unsigned := base64.RawURLEncoding.EncodeToString(headerJSON) + "." + base64.RawURLEncoding.EncodeToString(claimsJSON)
	signature := m.signature(unsigned)
	return unsigned + "." + signature, nil
}

func (m *Manager) verify(token string) (Claims, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return Claims{}, apperror.New(apperror.Unauthorized, "invalid access token")
	}
	unsigned := parts[0] + "." + parts[1]
	if !hmac.Equal([]byte(parts[2]), []byte(m.signature(unsigned))) {
		return Claims{}, apperror.New(apperror.Unauthorized, "invalid access token")
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return Claims{}, apperror.New(apperror.Unauthorized, "invalid access token")
	}
	var claims Claims
	if err := json.Unmarshal(payload, &claims); err != nil {
		return Claims{}, apperror.New(apperror.Unauthorized, "invalid access token")
	}
	if claims.Subject == "" || claims.ExpiresAt == 0 {
		return Claims{}, apperror.New(apperror.Unauthorized, "invalid access token")
	}
	return claims, nil
}

func (m *Manager) signature(unsigned string) string {
	mac := hmac.New(sha256.New, m.secret)
	_, _ = mac.Write([]byte(unsigned))
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}

func randomToken(bytesLen int) (string, error) {
	if bytesLen <= 0 {
		return "", errors.New("token length must be positive")
	}
	raw := make([]byte, bytesLen)
	if _, err := rand.Read(raw); err != nil {
		return "", fmt.Errorf("generate token: %w", err)
	}
	return base64.RawURLEncoding.EncodeToString(raw), nil
}
