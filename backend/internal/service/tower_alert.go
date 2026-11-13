package service

import (
	"context"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
)

type TowerObservation = toweralert.Observation
type TowerAlert = toweralert.Alert
type TowerAlertHistoryEntry = toweralert.HistoryEntry

type TowerAlertRepository interface {
	BeginScan(ctx context.Context, mapID string) (int64, error)
	Reconcile(ctx context.Context, mapID string, generation int64, now time.Time, observations []TowerObservation) ([]TowerAlert, error)
	ListForPlayer(ctx context.Context, playerID player.ID, limit int, before time.Time, beforeID string) ([]TowerAlert, error)
	ListHistoryForPlayer(ctx context.Context, playerID player.ID, limit int, before time.Time, beforeID string) ([]TowerAlertHistoryEntry, error)
	SetShare(ctx context.Context, towerID string, actor player.ID, allianceID alliance.ID, enabled bool) error
	PublishSharedIfEligible(ctx context.Context, eventID string, publish func() error) (bool, error)
}
