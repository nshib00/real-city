package handler

import (
	"encoding/json"
	"errors"
	"net/http"

	"real-city/backend/pkg/apperror"
)

type envelope map[string]any

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeError(w http.ResponseWriter, err error) {
	appErr := normalizeError(err)
	writeJSON(w, status(appErr.Kind), map[string]any{"error": appErr})
}

func decodeJSON(r *http.Request, dst any) error {
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(dst); err != nil {
		return apperror.Wrap(apperror.BadRequest, "invalid JSON request body", err)
	}
	return nil
}

func status(kind apperror.Kind) int {
	switch kind {
	case apperror.BadRequest, apperror.Validation:
		return http.StatusBadRequest
	case apperror.Unauthorized:
		return http.StatusUnauthorized
	case apperror.Forbidden:
		return http.StatusForbidden
	case apperror.NotFound:
		return http.StatusNotFound
	case apperror.Conflict:
		return http.StatusConflict
	case apperror.RateLimited:
		return http.StatusTooManyRequests
	default:
		return http.StatusInternalServerError
	}
}

func normalizeError(err error) *apperror.Error {
	var appErr *apperror.Error
	if errors.As(err, &appErr) {
		return appErr
	}
	return apperror.Wrap(apperror.Internal, "internal server error", err)
}
