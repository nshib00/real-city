package worker

import (
	"context"
	"encoding/json"
	"log/slog"
	"time"

	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

type OutboxDispatcher struct {
	repo   service.OutboxRepository
	events *service.EventBus
	log    *slog.Logger
	cfg    config.SimulationConfig
	now    func() time.Time
}

func NewOutboxDispatcher(repo service.OutboxRepository, events *service.EventBus, log *slog.Logger, cfg config.SimulationConfig) *OutboxDispatcher {
	if cfg.TickInterval <= 0 {
		cfg.TickInterval = time.Second
	}
	if cfg.BatchSize <= 0 {
		cfg.BatchSize = 100
	}
	if cfg.LockTTL <= 0 {
		cfg.LockTTL = 15 * time.Second
	}
	return &OutboxDispatcher{repo: repo, events: events, log: log, cfg: cfg, now: func() time.Time { return time.Now().UTC() }}
}

func (d *OutboxDispatcher) Run(ctx context.Context) error {
	ticker := time.NewTicker(d.cfg.TickInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			_, _ = d.Dispatch(ctx)
		}
	}
}

func (d *OutboxDispatcher) Dispatch(ctx context.Context) (processed int, resultErr error) {
	started := time.Now()
	defer func() { observability.Dispatch("total", started, resultErr) }()
	now := d.now()
	fetchStarted := time.Now()
	items, err := d.repo.FetchDue(ctx, now, d.cfg.BatchSize, d.cfg.LockTTL)
	observability.Dispatch("fetch", fetchStarted, err)
	if err != nil {
		d.log.Warn("outbox.dispatch.fetch_failed", "event", "outbox.dispatch.fetch_failed", "error", err.Error())
		return 0, err
	}
	for range items {
		observability.Outbox("fetched")
	}
	for _, item := range items {
		publishStarted := time.Now()
		publishErr := d.publish(item)
		observability.Dispatch("publish", publishStarted, publishErr)
		if err := publishErr; err != nil {
			if item.Attempts >= 5 {
				if markErr := d.repo.MarkDead(ctx, item.ID, err.Error(), now); markErr != nil {
					observability.Outbox("failed")
					return 0, markErr
				}
				observability.Outbox("dead")
				d.log.Warn("outbox.dispatch.dead", "event", "outbox.dispatch.dead", "event_id", item.ID, "attempts", item.Attempts+1, "error", err.Error())
				continue
			}
			retryAt := now.Add(time.Duration(item.Attempts+1) * time.Second)
			if markErr := d.repo.MarkFailed(ctx, item.ID, err.Error(), retryAt, now); markErr != nil {
				observability.Outbox("failed")
				return 0, markErr
			}
			observability.Outbox("retried")
			d.log.Warn("outbox.dispatch.failed", "event", "outbox.dispatch.failed", "event_id", item.ID, "retry_at", retryAt, "error", err.Error())
			continue
		}
		if err := d.repo.MarkSent(ctx, item.ID, now); err != nil {
			observability.Outbox("failed")
			return 0, err
		}
		observability.Outbox("sent")
		d.log.Info("outbox.dispatch.sent", "event", "outbox.dispatch.sent", "event_id", item.ID, "event_type", item.Type)
	}
	return len(items), nil
}

func (d *OutboxDispatcher) publish(item outbox.OutboxEvent) error {
	payload := map[string]any{}
	if len(item.Payload) > 0 {
		if err := json.Unmarshal(item.Payload, &payload); err != nil {
			return err
		}
	}
	d.events.Publish(service.Event{
		Type:      service.EventType(item.Type),
		ChunkID:   item.ChunkID,
		PlayerID:  player.ID(item.PlayerID),
		Alliance:  item.Alliance,
		Payload:   payload,
		CreatedAt: item.CreatedAt,
	})
	return nil
}
