package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
)

type towerAlertKey struct{ mapID, ownerID, monsterID string }
type towerScanState struct{ next, applied int64 }

type TowerAlertRepo struct {
	mu        sync.Mutex
	scans     map[string]towerScanState
	states    map[towerAlertKey]toweralert.State
	incidents []toweralert.Alert
}

func NewTowerAlertRepo() *TowerAlertRepo {
	return &TowerAlertRepo{scans: make(map[string]towerScanState), states: make(map[towerAlertKey]toweralert.State)}
}

func (r *TowerAlertRepo) BeginScan(_ context.Context, mapID string) (int64, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	scan := r.scans[mapID]
	scan.next++
	r.scans[mapID] = scan
	return scan.next, nil
}

func (r *TowerAlertRepo) Reconcile(_ context.Context, mapID string, generation int64, now time.Time, observations []toweralert.Observation) ([]toweralert.Alert, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	scan := r.scans[mapID]
	if generation <= scan.applied || generation > scan.next {
		return nil, nil
	}
	seen := make(map[towerAlertKey]bool, len(observations))
	created := make([]toweralert.Alert, 0)
	for _, observation := range observations {
		key := towerAlertKey{mapID, string(observation.OwnerID), observation.MonsterID}
		if seen[key] {
			continue
		}
		seen[key] = true
		state, alert := toweralert.Advance(r.states[key], now)
		r.states[key] = state
		if !alert {
			continue
		}
		item := toweralert.Alert{
			IncidentID: toweralert.IncidentID(mapID, observation.OwnerID, observation.MonsterID, state.Episode),
			OwnerID:    observation.OwnerID, TowerID: observation.TowerID, MonsterID: observation.MonsterID,
			MonsterType: observation.MonsterType, TileX: observation.TileX, TileY: observation.TileY,
			TargetBuildingID: observation.TargetBuildingID, DetectedAt: now,
		}
		r.incidents = append(r.incidents, item)
		created = append(created, item)
	}
	for key, state := range r.states {
		if key.mapID == mapID && state.Inside && !seen[key] {
			state.Inside = false
			r.states[key] = state
		}
	}
	scan.applied = generation
	r.scans[mapID] = scan
	return created, nil
}

func (r *TowerAlertRepo) ListForPlayer(_ context.Context, playerID player.ID, limit int, before time.Time, beforeID string) ([]toweralert.Alert, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	items := make([]toweralert.Alert, 0)
	for _, item := range r.incidents {
		if item.OwnerID != playerID {
			continue
		}
		if !before.IsZero() && (item.DetectedAt.After(before) || item.DetectedAt.Equal(before) && item.IncidentID >= beforeID) {
			continue
		}
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].DetectedAt.Equal(items[j].DetectedAt) {
			return items[i].IncidentID > items[j].IncidentID
		}
		return items[i].DetectedAt.After(items[j].DetectedAt)
	})
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}
