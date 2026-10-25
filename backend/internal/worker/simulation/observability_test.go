package simulation

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

type failingActions struct{ service.ActionRepository }

func (failingActions) FetchDue(context.Context, time.Time, int, time.Duration) ([]action.GameAction, error) {
	return nil, errors.New("test fetch failure")
}

func tickCount(t *testing.T, result string) float64 {
	t.Helper()
	response := httptest.NewRecorder()
	observability.WorkerHandler(nil).ServeHTTP(response, httptest.NewRequest("GET", "/metrics", nil))
	prefix := `real_city_simulation_ticks_total{mode="catch_up",result="` + result + `"} `
	for _, line := range strings.Split(response.Body.String(), "\n") {
		if strings.HasPrefix(line, prefix) {
			value, err := strconv.ParseFloat(strings.TrimPrefix(line, prefix), 64)
			if err != nil {
				t.Fatal(err)
			}
			return value
		}
	}
	t.Fatalf("missing %s", prefix)
	return 0
}

func TestTickMetricsSuccessAndFailure(t *testing.T) {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	config := config.SimulationConfig{BatchSize: 1, TickInterval: time.Second}
	okBefore := tickCount(t, "ok")
	errorBefore := tickCount(t, "error")
	if _, err := NewRunner(nil, nil, nil, nil, nil, logger, config).Tick(context.Background()); err != nil {
		t.Fatal(err)
	}
	if _, err := NewRunner(failingActions{}, nil, nil, nil, nil, logger, config).Tick(context.Background()); err == nil {
		t.Fatal("expected failed tick")
	}
	if got := tickCount(t, "ok"); got != okBefore+1 {
		t.Fatalf("ok tick count = %v, want %v", got, okBefore+1)
	}
	if got := tickCount(t, "error"); got != errorBefore+1 {
		t.Fatalf("error tick count = %v, want %v", got, errorBefore+1)
	}
}
