package ws

import (
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"

	"real-city/backend/internal/service"
)

func TestGatewayUpgradeFailureMetric(t *testing.T) {
	gateway := NewGateway(nil, service.NewEventBus(1), slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer gateway.Shutdown()
	response := httptest.NewRecorder()
	gateway.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/realtime?token=private", nil))
	if response.Code != http.StatusUnauthorized {
		t.Fatalf("status = %d", response.Code)
	}
	stats := gateway.Stats()
	if stats.Transport.UpgradeAuthFailures != 1 || stats.Transport.UpgradesOK != 0 {
		t.Fatalf("upgrade stats = %+v", stats.Transport)
	}
}

func TestFanoutHistogramConcurrentObservations(t *testing.T) {
	var metrics TransportMetrics
	var group sync.WaitGroup
	for range 8 {
		group.Add(1)
		go func() {
			defer group.Done()
			for range 100 {
				metrics.ObserveFanout(3)
				_ = metrics.Snapshot()
			}
		}()
	}
	group.Wait()
	stats := metrics.Snapshot()
	if stats.FanoutBuckets[2] != 0 || stats.FanoutBuckets[3] != 800 || stats.FanoutBuckets[len(stats.FanoutBuckets)-1] != 800 {
		t.Fatalf("fanout buckets = %+v", stats.FanoutBuckets)
	}
}
