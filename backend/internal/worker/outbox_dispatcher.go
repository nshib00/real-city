package worker

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"time"

	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/observability"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/config"
)

type OutboxDispatcher struct {
	repo        service.OutboxRepository
	events      *service.EventBus
	log         *slog.Logger
	cfg         config.SimulationConfig
	now         func() time.Time
	sharedGuard func(context.Context, string, func() error) (bool, error)
}

func (d *OutboxDispatcher) SetSharedTowerGuard(guard func(context.Context, string, func() error) (bool, error)) {
	d.sharedGuard = guard
}

func NewOutboxDispatcher(repo service.OutboxRepository, events *service.EventBus, log *slog.Logger, cfg config.SimulationConfig) *OutboxDispatcher {
	if cfg.OutboxDispatchInterval <= 0 {
		cfg.OutboxDispatchInterval = 500 * time.Millisecond
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
	ticker := time.NewTicker(d.cfg.OutboxDispatchInterval)
	defer ticker.Stop()
	pruneTicker := time.NewTicker(10 * time.Second)
	defer pruneTicker.Stop()
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			_, _ = d.Dispatch(ctx)
		case <-pruneTicker.C:
			if _, err := d.repo.PruneSent(ctx, d.now().Add(-time.Hour), 10000); err != nil && ctx.Err() == nil {
				d.log.Warn("outbox.prune.failed", "event", "outbox.prune.failed", "error", err)
			}
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
		var publishErr error
		if service.EventType(item.Type) == service.EventTowerThreatShared && d.sharedGuard != nil {
			_, publishErr = d.sharedGuard(ctx, string(item.ID), func() error { return d.publish(item) })
		} else if service.EventType(item.Type) == service.EventTowerThreatShared {
			publishErr = errors.New("shared tower delivery guard is missing")
		} else {
			publishErr = d.publish(item)
		}
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
	payload, err := decodePayload(item)
	if err != nil {
		return err
	}
	return d.events.Publish(service.Event{
		Type:      service.EventType(item.Type),
		ChunkID:   item.ChunkID,
		PlayerID:  player.ID(item.PlayerID),
		Alliance:  item.Alliance,
		Payload:   payload,
		CreatedAt: item.CreatedAt,
	})
}

func decodePayload(item outbox.OutboxEvent) (any, error) {
	var payload any
	switch service.EventType(item.Type) {
	case service.EventTileChanged:
		payload = &service.TileChangedPayload{}
	case service.EventBuildingPlaced, service.EventBuildingUpdated:
		payload = &service.BuildingPayload{}
	case service.EventBuildingRemoved:
		payload = &service.BuildingRemovedPayload{}
	case service.EventResourceChanged:
		payload = &service.ResourceChangedPayload{}
	case service.EventProductionDone:
		payload = &service.ProductionPayload{}
	case service.EventInventoryChanged:
		payload = &service.InventoryPayload{}
	case service.EventPresenceChanged:
		payload = &service.PresencePayload{}
	case service.EventMonsterSpawned, service.EventMonsterMoved, service.EventMonsterAttacked,
		service.EventMonsterDamaged, service.EventMonsterDied, service.EventMonsterDespawned:
		payload = &service.MonsterPayload{}
	case service.EventMonsterLootDropped, service.EventMonsterLootClaimed:
		payload = &service.MonsterLootPayload{}
	case service.EventCannonShot:
		payload = &service.CannonShotPayload{}
	case service.EventDefenseTriggered:
		payload = &service.DefenseTriggeredPayload{}
	case service.EventTowerThreatDetected:
		payload = &service.TowerThreatPayload{}
	case service.EventTowerThreatShared:
		payload = &service.TowerSharedThreatPayload{}
	default:
		payload = &map[string]any{}
	}
	if len(item.Payload) > 0 {
		if err := json.Unmarshal(item.Payload, payload); err != nil {
			return nil, err
		}
	}
	switch typed := payload.(type) {
	case *service.TileChangedPayload:
		return *typed, nil
	case *service.BuildingPayload:
		return *typed, nil
	case *service.BuildingRemovedPayload:
		return *typed, nil
	case *service.ResourceChangedPayload:
		return *typed, nil
	case *service.ProductionPayload:
		return *typed, nil
	case *service.InventoryPayload:
		return *typed, nil
	case *service.PresencePayload:
		return *typed, nil
	case *service.MonsterPayload:
		return *typed, nil
	case *service.MonsterLootPayload:
		return *typed, nil
	case *service.CannonShotPayload:
		return *typed, nil
	case *service.DefenseTriggeredPayload:
		return *typed, nil
	case *service.TowerThreatPayload:
		return *typed, nil
	case *service.TowerSharedThreatPayload:
		return *typed, nil
	default:
		return *payload.(*map[string]any), nil
	}
}
