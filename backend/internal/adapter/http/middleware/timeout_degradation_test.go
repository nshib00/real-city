package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestSlowDependencyReturnsBoundedTimeout(t *testing.T) {
	handler := Timeout(10 * time.Millisecond)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		<-r.Context().Done()
	}))
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/world/chunks", nil))
	if response.Code != http.StatusServiceUnavailable {
		t.Fatalf("status = %d, want 503", response.Code)
	}
	if response.Body.String() != `{"error":{"kind":"timeout","message":"request timed out"}}` {
		t.Fatalf("body = %q", response.Body.String())
	}
}
