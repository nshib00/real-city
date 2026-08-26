package ws

import (
	"strings"
	"time"

	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/domain/player"
)

func AuthenticateBearer(tokens *jwtadapter.Manager, header string) (player.ID, error) {
	raw := strings.TrimSpace(strings.TrimPrefix(header, "Bearer "))
	claims, err := tokens.VerifyAccess(raw, time.Now().UTC())
	if err != nil {
		return "", err
	}
	return claims.Subject, nil
}
