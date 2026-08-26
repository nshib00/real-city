package httpadapter

import (
	"net/http"
	"testing"

	"real-city/backend/pkg/apperror"
)

func TestStatusMapsApplicationErrors(t *testing.T) {
	if got := Status(apperror.Forbidden); got != http.StatusForbidden {
		t.Fatalf("expected 403, got %d", got)
	}
	if got := Status(apperror.RateLimited); got != http.StatusTooManyRequests {
		t.Fatalf("expected 429, got %d", got)
	}
}
