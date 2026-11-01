package httpadapter

import (
	"context"
	"time"
)

type databasePinger interface {
	PingContext(context.Context) error
}

// A stalled database driver may not return when its context expires. Limit the
// number of outstanding probes so health checks cannot exhaust the DB pool.
type readinessProbe struct {
	db   databasePinger
	busy chan struct{}
}

func newReadinessProbe(db databasePinger) *readinessProbe {
	return &readinessProbe{db: db, busy: make(chan struct{}, 1)}
}

func (p *readinessProbe) ready(ctx context.Context) bool {
	if p.db == nil {
		return true
	}
	select {
	case p.busy <- struct{}{}:
	default:
		return false
	}
	probeCtx, cancel := context.WithTimeout(ctx, time.Second)
	defer cancel()
	result := make(chan error, 1)
	go func() {
		defer func() { <-p.busy }()
		result <- p.db.PingContext(probeCtx)
	}()
	select {
	case err := <-result:
		return err == nil && probeCtx.Err() == nil
	case <-probeCtx.Done():
		return false
	}
}
