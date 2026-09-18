package middleware

import (
	"log/slog"
	"net/http"
	"strconv"
	"time"
)

func Logger(log *slog.Logger) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			recorder := &ResponseRecorder{ResponseWriter: w, StatusCode: http.StatusOK}
			next.ServeHTTP(recorder, r)
			pattern := r.Pattern
			if pattern == "" {
				pattern = "unmatched"
			}
			log.Info("http.request",
				"event", "http.request",
				"request_id", RequestIDFromContext(r.Context()),
				"method", r.Method,
				"path", r.URL.Path,
				"route_pattern", pattern,
				"status", recorder.StatusCode,
				"status_class", strconv.Itoa(recorder.StatusCode/100)+"xx",
				"response_size", recorder.Size,
				"duration_ms", time.Since(start).Milliseconds(),
				"panic", recorder.Panic,
				"ip", r.RemoteAddr,
				"user_agent", r.UserAgent(),
			)
		})
	}
}

type ResponseRecorder struct {
	http.ResponseWriter
	StatusCode int
	Size       int
	Panic      bool
}

func (r *ResponseRecorder) WriteHeader(status int) {
	r.StatusCode = status
	r.ResponseWriter.WriteHeader(status)
}

func (r *ResponseRecorder) Write(data []byte) (int, error) {
	written, err := r.ResponseWriter.Write(data)
	r.Size += written
	return written, err
}

func (r *ResponseRecorder) MarkPanic() {
	r.Panic = true
}
