package httpadapter

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type testPinger struct {
	started chan struct{}
	release chan struct{}
	once    sync.Once
	calls   atomic.Int32
	err     error
}

func (p *testPinger) PingContext(context.Context) error {
	p.calls.Add(1)
	if p.started != nil {
		p.once.Do(func() { close(p.started) })
		<-p.release // Simulate a driver that ignores cancellation.
	}
	return p.err
}

func TestReadinessProbeBoundsStalledDriver(t *testing.T) {
	pinger := &testPinger{started: make(chan struct{}), release: make(chan struct{})}
	probe := newReadinessProbe(pinger)
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	start := time.Now()
	if probe.ready(ctx) {
		t.Fatal("stalled database reported ready")
	}
	if time.Since(start) > time.Second {
		t.Fatal("readiness exceeded its deadline")
	}
	<-pinger.started
	if probe.ready(context.Background()) || pinger.calls.Load() != 1 {
		t.Fatal("started a second probe while the first is blocked")
	}
	close(pinger.release)
	deadline := time.After(time.Second)
	for len(probe.busy) != 0 {
		select {
		case <-deadline:
			t.Fatal("probe slot was not released")
		default:
			time.Sleep(time.Millisecond)
		}
	}
	if !probe.ready(context.Background()) {
		t.Fatal("database did not recover")
	}
}

func TestReadinessProbeFailureAndNoDatabase(t *testing.T) {
	if !newReadinessProbe(nil).ready(context.Background()) {
		t.Fatal("nil database should preserve dev readiness")
	}
	if newReadinessProbe(&testPinger{err: errors.New("down")}).ready(context.Background()) {
		t.Fatal("failed ping reported ready")
	}
}
