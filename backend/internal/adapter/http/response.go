package httpadapter

import (
	"encoding/json"
	"errors"
	"net/http"

	"real-city/backend/pkg/apperror"
)

type Envelope map[string]any

type ErrorResponse struct {
	Error apperror.Error `json:"error"`
}

type PageMeta struct {
	Limit  int `json:"limit"`
	Offset int `json:"offset"`
	Total  int `json:"total,omitempty"`
}

func JSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func Error(w http.ResponseWriter, err error) {
	appErr := normalizeError(err)
	JSON(w, Status(appErr.Kind), ErrorResponse{Error: *appErr})
}

func DecodeJSON(r *http.Request, dst any) error {
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(dst); err != nil {
		return apperror.Wrap(apperror.BadRequest, "invalid JSON request body", err)
	}
	return nil
}

func Status(kind apperror.Kind) int {
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
