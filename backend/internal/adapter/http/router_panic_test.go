package httpadapter

import (
	"bytes"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"real-city/backend/internal/adapter/http/middleware"
)

func TestRecoveredPanicLogRespectsEnvironment(t *testing.T) {
	for _, test := range []struct {
		appEnv    string
		contains  string
		forbidden string
	}{
		{"development", "secret-panic", ""},
		{"production", "http.panic", "secret-panic"},
	} {
		t.Run(test.appEnv, func(t *testing.T) {
			var output bytes.Buffer
			logger := slog.New(slog.NewJSONHandler(&output, nil))
			request := httptest.NewRequest(http.MethodGet, "/private/secret-path", nil)
			request.Header.Set("X-Request-ID", "panic-test-id")
			middleware.RequestID()(http.HandlerFunc(func(_ http.ResponseWriter, r *http.Request) {
				logRecoveredPanic(logger, test.appEnv, r, "secret-panic", []byte("secret-stack"))
			})).ServeHTTP(httptest.NewRecorder(), request)
			message := output.String()
			if !strings.Contains(message, test.contains) || !strings.Contains(message, "panic-test-id") {
				t.Fatalf("missing panic marker or request id: %s", message)
			}
			if test.forbidden != "" && (strings.Contains(message, test.forbidden) || strings.Contains(message, "secret-stack") || strings.Contains(message, "secret-path")) {
				t.Fatalf("production panic log contains sensitive details: %s", message)
			}
		})
	}
}
