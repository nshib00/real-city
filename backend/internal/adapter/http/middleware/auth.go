package middleware

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/domain/player"
	"real-city/backend/pkg/apperror"
)

type contextKey string

const playerIDKey contextKey = "player_id"

func Auth(tokens *jwtadapter.Manager, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw := strings.TrimSpace(strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer "))
		if raw == "" || raw == r.Header.Get("Authorization") {
			writeAuthError(w, apperror.New(apperror.Unauthorized, "authorization bearer token is required"))
			return
		}
		claims, err := tokens.VerifyAccess(raw, time.Now().UTC())
		if err != nil {
			writeAuthError(w, err)
			return
		}
		next.ServeHTTP(w, r.WithContext(WithPlayerID(r.Context(), claims.Subject)))
	})
}

func WithPlayerID(ctx context.Context, id player.ID) context.Context {
	return context.WithValue(ctx, playerIDKey, id)
}

func PlayerID(ctx context.Context) (player.ID, bool) {
	id, ok := ctx.Value(playerIDKey).(player.ID)
	return id, ok
}

func writeAuthError(w http.ResponseWriter, err error) {
	appErr, ok := err.(*apperror.Error)
	if !ok {
		appErr = apperror.New(apperror.Unauthorized, "unauthorized")
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnauthorized)
	_ = json.NewEncoder(w).Encode(map[string]any{"error": appErr})
}
