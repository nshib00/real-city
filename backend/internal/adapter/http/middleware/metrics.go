package middleware

import (
	"net/http"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

var DurationBuckets = [...]float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5}

type HTTPMetrics struct {
	mu       sync.RWMutex
	requests map[httpMetricKey]httpMetricValue
	inFlight atomic.Int64
}

type httpMetricKey struct {
	Method      string
	Route       string
	StatusClass string
}

type httpMetricValue struct {
	Count           uint64
	DurationMillis  uint64
	ResponseBytes   uint64
	DurationSeconds float64
	Buckets         [len(DurationBuckets)]uint64
}

type HTTPMetricSample struct {
	Method          string
	Route           string
	StatusClass     string
	Count           uint64
	DurationMillis  uint64
	ResponseBytes   uint64
	DurationSeconds float64
	Buckets         [len(DurationBuckets)]uint64
}

func NewHTTPMetrics() *HTTPMetrics {
	return &HTTPMetrics{requests: make(map[httpMetricKey]httpMetricValue)}
}

func (m *HTTPMetrics) Observe(method string, route string, status int, duration time.Duration, responseBytes int) {
	if m == nil {
		return
	}
	if route == "" {
		route = "unmatched"
	}
	switch method {
	case http.MethodGet, http.MethodPost, http.MethodPatch, http.MethodPut, http.MethodDelete, http.MethodHead, http.MethodOptions:
	default:
		method = "OTHER"
	}
	key := httpMetricKey{
		Method:      method,
		Route:       route,
		StatusClass: strconv.Itoa(status/100) + "xx",
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	value := m.requests[key]
	value.Count++
	value.DurationMillis += uint64(duration.Milliseconds())
	value.DurationSeconds += duration.Seconds()
	for i, bound := range DurationBuckets {
		if duration.Seconds() <= bound {
			value.Buckets[i]++
		}
	}
	if responseBytes > 0 {
		value.ResponseBytes += uint64(responseBytes)
	}
	m.requests[key] = value
}

func (m *HTTPMetrics) Samples() []HTTPMetricSample {
	if m == nil {
		return nil
	}
	m.mu.RLock()
	defer m.mu.RUnlock()
	samples := make([]HTTPMetricSample, 0, len(m.requests))
	for key, value := range m.requests {
		samples = append(samples, HTTPMetricSample{
			Method:          key.Method,
			Route:           key.Route,
			StatusClass:     key.StatusClass,
			Count:           value.Count,
			DurationMillis:  value.DurationMillis,
			ResponseBytes:   value.ResponseBytes,
			DurationSeconds: value.DurationSeconds,
			Buckets:         value.Buckets,
		})
	}
	return samples
}

func (m *HTTPMetrics) InFlight() int64 { return m.inFlight.Load() }

func Metrics(metrics *HTTPMetrics, mux *http.ServeMux) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/metrics" || r.URL.Path == "/api/v1/realtime" {
				next.ServeHTTP(w, r)
				return
			}
			_, pattern := mux.Handler(r)
			if !registeredPattern(pattern) {
				pattern = "unmatched"
			}
			r.Pattern = pattern
			metrics.inFlight.Add(1)
			start := time.Now()
			recorder := &ResponseRecorder{ResponseWriter: w, StatusCode: http.StatusOK}
			panicking := true
			defer func() {
				metrics.inFlight.Add(-1)
				if panicking {
					recorder.StatusCode = http.StatusInternalServerError
				}
				metrics.Observe(r.Method, pattern, recorder.StatusCode, time.Since(start), recorder.Size)
			}()
			next.ServeHTTP(recorder, r)
			panicking = false
		})
	}
}

// ServeMux.Handler returns a raw redirect destination for non-canonical paths.
// Registered routes in this application always start with a method and space.
func registeredPattern(pattern string) bool {
	for _, method := range [...]string{"GET ", "POST ", "PATCH ", "DELETE "} {
		if strings.HasPrefix(pattern, method+"/") {
			return true
		}
	}
	return false
}
