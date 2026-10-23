package httpadapter

import (
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"real-city/backend/internal/adapter/http/middleware"
)

func TestMetricsExpositionAndRouteLabels(t *testing.T) {
	router := NewRouter(slog.New(slog.NewTextHandler(io.Discard, nil)), RouterDeps{})
	for _, path := range []string{"/health", "/unknown?player_id=private", "/metrics"} {
		response := httptest.NewRecorder()
		router.ServeHTTP(response, httptest.NewRequest(http.MethodGet, path, nil))
	}
	response := httptest.NewRecorder()
	router.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	body := response.Body.String()
	if got := response.Code; got != http.StatusOK {
		t.Fatalf("metrics status = %d", got)
	}
	for _, want := range []string{
		"# HELP real_city_http_request_duration_seconds ",
		"# TYPE real_city_http_request_duration_seconds histogram",
		`real_city_http_requests_total{method="GET",route="GET /health",status_class="2xx"} 1`,
		`real_city_http_requests_total{method="GET",route="unmatched",status_class="4xx"} 1`,
		`real_city_http_request_duration_seconds_bucket{le="+Inf",method="GET",route="GET /health",status_class="2xx"} 1`,
	} {
		if !strings.Contains(body, want) {
			t.Errorf("missing metric %q", want)
		}
	}
	if strings.Contains(body, "private") || strings.Contains(body, `route="GET /metrics"`) {
		t.Fatal("raw query or self-scrape route leaked into metrics")
	}
}

func TestHTTPMetricsRecordsPanics(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /panic", func(http.ResponseWriter, *http.Request) { panic("boom") })
	metrics := middleware.NewHTTPMetrics()
	handler := middleware.Metrics(metrics, mux)(mux)
	func() {
		defer func() { _ = recover() }()
		handler.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/panic", nil))
	}()
	samples := metrics.Samples()
	if len(samples) != 1 || samples[0].StatusClass != "5xx" || samples[0].Count != 1 || metrics.InFlight() != 0 {
		t.Fatalf("panic metrics = %+v, in flight = %d", samples, metrics.InFlight())
	}
	if samples[0].DurationSeconds < 0 || samples[0].DurationSeconds > 1 {
		t.Fatalf("invalid duration: %f", samples[0].DurationSeconds)
	}
}

func TestHTTPMetricsConcurrentObservations(t *testing.T) {
	metrics := middleware.NewHTTPMetrics()
	const workers, observations = 16, 100
	var group sync.WaitGroup
	for range workers {
		group.Add(1)
		go func() {
			defer group.Done()
			for range observations {
				metrics.Observe(http.MethodGet, "GET /health", http.StatusOK, 0, 12)
				_ = metrics.Samples()
			}
		}()
	}
	group.Wait()
	samples := metrics.Samples()
	if len(samples) != 1 || samples[0].Count != workers*observations || samples[0].Buckets[0] != workers*observations || samples[0].ResponseBytes != workers*observations*12 {
		t.Fatalf("unexpected concurrent snapshot: %+v", samples)
	}
}

func BenchmarkMetricsExposition(b *testing.B) {
	stats := middleware.NewHTTPMetrics()
	for range 1000 {
		stats.Observe(http.MethodGet, "GET /api/v1/world/viewport", http.StatusOK, 2*time.Millisecond, 512)
	}
	handler := metrics(stats, nil, nil)
	request := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	b.ReportAllocs()
	b.ResetTimer()
	for range b.N {
		handler.ServeHTTP(httptest.NewRecorder(), request)
	}
}
