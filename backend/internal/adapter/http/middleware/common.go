package middleware

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"runtime/debug"
	"strings"
	"time"

	"real-city/backend/pkg/apperror"
)

type Middleware func(http.Handler) http.Handler

func Chain(handler http.Handler, items ...Middleware) http.Handler {
	for i := len(items) - 1; i >= 0; i-- {
		handler = items[i](handler)
	}
	return handler
}

func CORS(allowedOrigins []string) Middleware {
	allowed := map[string]struct{}{}
	for _, origin := range allowedOrigins {
		allowed[origin] = struct{}{}
	}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")
			_, wildcard := allowed["*"]
			_, exact := allowed[origin]
			if origin != "" && !wildcard && !exact {
				http.Error(w, "origin is not allowed", http.StatusForbidden)
				return
			}
			if origin != "" && wildcard {
				w.Header().Set("Access-Control-Allow-Origin", "*")
			} else if origin != "" && exact {
				w.Header().Set("Access-Control-Allow-Origin", origin)
			}
			w.Header().Add("Vary", "Origin")
			w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type, Idempotency-Key, X-Request-ID")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
			if r.Method == http.MethodOptions {
				w.WriteHeader(http.StatusNoContent)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func RequestID() Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			id := strings.TrimSpace(r.Header.Get("X-Request-ID"))
			if id == "" {
				id = randomID()
			}
			w.Header().Set("X-Request-ID", id)
			next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), requestIDKey, id)))
		})
	}
}

func BodyLimit(maxBytes int64) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.Body != nil {
				r.Body = http.MaxBytesReader(w, r.Body, maxBytes)
			}
			next.ServeHTTP(w, r)
		})
	}
}

func Timeout(duration time.Duration) Middleware {
	return func(next http.Handler) http.Handler {
		timed := http.TimeoutHandler(next, duration, `{"error":{"kind":"timeout","message":"request timed out"}}`)
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/api/v1/realtime" {
				next.ServeHTTP(w, r)
				return
			}
			timed.ServeHTTP(w, r)
		})
	}
}

func Recoverer(onPanic func(*http.Request, any, []byte)) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			defer func() {
				if recovered := recover(); recovered != nil {
					stack := debug.Stack()
					if marker, ok := w.(interface{ MarkPanic() }); ok {
						marker.MarkPanic()
					}
					if onPanic != nil {
						onPanic(r, recovered, stack)
					}
					writeMiddlewareError(w, http.StatusInternalServerError, apperror.New(apperror.Internal, "internal server error"))
				}
			}()
			next.ServeHTTP(w, r)
		})
	}
}

type requestIDContextKey string

const requestIDKey requestIDContextKey = "request_id"

func RequestIDFromContext(ctx context.Context) string {
	id, _ := ctx.Value(requestIDKey).(string)
	return id
}

func writeMiddlewareError(w http.ResponseWriter, status int, err *apperror.Error) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]any{"error": err})
}

func randomID() string {
	var buf [16]byte
	if _, err := rand.Read(buf[:]); err != nil {
		return hex.EncodeToString([]byte(time.Now().UTC().Format(time.RFC3339Nano)))
	}
	return hex.EncodeToString(buf[:])
}
