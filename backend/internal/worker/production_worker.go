package worker

import (
	"context"
	"log/slog"
	"time"
)

type ProductionWorker struct {
	log      *slog.Logger
	interval time.Duration
}

func NewProductionWorker(log *slog.Logger, interval time.Duration) *ProductionWorker {
	return &ProductionWorker{log: log, interval: interval}
}

func (w *ProductionWorker) Run(ctx context.Context) error {
	ticker := time.NewTicker(w.interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			w.log.Info("economy.production.tick", "event", "economy.production.tick")
		}
	}
}
