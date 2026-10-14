package middleware

import (
	"net/http"
	"strconv"
	"sync"
	"time"
)

type HTTPMetrics struct {
	mu       sync.RWMutex
	requests map[httpMetricKey]httpMetricValue
}

type httpMetricKey struct {
	Method      string
	Route       string
	StatusClass string
}

type httpMetricValue struct {
	Count          uint64
	DurationMillis uint64
	ResponseBytes  uint64
}

type HTTPMetricSample struct {
	Method         string
	Route          string
	StatusClass    string
	Count          uint64
	DurationMillis uint64
	ResponseBytes  uint64
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
			Method:         key.Method,
			Route:          key.Route,
			StatusClass:    key.StatusClass,
			Count:          value.Count,
			DurationMillis: value.DurationMillis,
			ResponseBytes:  value.ResponseBytes,
		})
	}
	return samples
}

func Metrics(metrics *HTTPMetrics) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			recorder := &ResponseRecorder{ResponseWriter: w, StatusCode: http.StatusOK}
			next.ServeHTTP(recorder, r)
			metrics.Observe(r.Method, r.Pattern, recorder.StatusCode, time.Since(start), recorder.Size)
		})
	}
}
