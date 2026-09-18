package simulation

import (
	"testing"
	"time"
)

func TestWindleafProgressBecomesReady(t *testing.T) {
	planted := time.Date(2026, 8, 25, 10, 0, 0, 0, time.UTC)
	progress := WindleafProgress(planted, planted.Add(10*time.Minute))
	if !progress.Ready || !progress.Stage.Ready {
		t.Fatalf("expected ready crop: %#v", progress)
	}
}
