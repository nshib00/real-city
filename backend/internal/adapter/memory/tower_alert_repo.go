package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

type towerAlertKey struct{ mapID, ownerID, monsterID string }
type towerScanState struct{ next, applied int64 }
type towerShare struct {
	allianceID alliance.ID
	joinedAt   time.Time
	enabled    bool
	version    int64
}

type TowerAlertRepo struct {
	mu            sync.Mutex
	scans         map[string]towerScanState
	states        map[towerAlertKey]toweralert.State
	incidents     []toweralert.Alert
	shares        map[string]towerShare
	shared        map[player.ID][]toweralert.SharedAlert
	buildings     *BuildingRepo
	social        *SocialRepo
	publishShared func(player.ID, toweralert.SharedAlert) error
}

func NewTowerAlertRepo() *TowerAlertRepo {
	return &TowerAlertRepo{scans: make(map[string]towerScanState), states: make(map[towerAlertKey]toweralert.State), shares: make(map[string]towerShare), shared: make(map[player.ID][]toweralert.SharedAlert)}
}

func (r *TowerAlertRepo) SetAllySources(buildings *BuildingRepo, social *SocialRepo, publish func(player.ID, toweralert.SharedAlert) error) {
	r.buildings, r.social, r.publishShared = buildings, social, publish
}

func (r *TowerAlertRepo) BeginScan(_ context.Context, mapID string) (int64, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	scan := r.scans[mapID]
	scan.next++
	r.scans[mapID] = scan
	return scan.next, nil
}

func (r *TowerAlertRepo) Reconcile(ctx context.Context, mapID string, generation int64, now time.Time, observations []toweralert.Observation) ([]toweralert.Alert, error) {
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
			TargetBuildingID: observation.TargetBuildingID, RelayTowerIDs: append([]string{}, observation.RelayTowerIDs...), DetectedAt: now,
		}
		r.incidents = append(r.incidents, item)
		if err := r.shareIncident(ctx, item, observation); err != nil {
			return nil, err
		}
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

func (r *TowerAlertRepo) shareIncident(ctx context.Context, item toweralert.Alert, observation toweralert.Observation) error {
	if r.buildings == nil || r.social == nil {
		return nil
	}
	share := r.shares[observation.TowerID]
	if !share.enabled {
		return nil
	}
	source, err := r.buildings.FindByID(ctx, building.ID(observation.TowerID))
	if err != nil || source.OwnerID != string(observation.OwnerID) || source.Level != 6 || !toweralert.ActiveTower(source) {
		return nil
	}
	allianceItem, member, err := r.social.FindByPlayer(ctx, observation.OwnerID)
	if err != nil || allianceItem.ID != share.allianceID || !member.JoinedAt.Equal(share.joinedAt) {
		return nil
	}
	structures, err := r.buildings.ListByMap(ctx, source.MapID)
	if err != nil {
		return err
	}
	sort.Slice(structures, func(i, j int) bool { return structures[i].ID < structures[j].ID })
	region := world.ChunkForTile(world.Coord{X: item.TileX, Y: item.TileY})
	shared := toweralert.SharedAlert{IncidentID: item.IncidentID, MonsterType: item.MonsterType, RegionX: region.X, RegionY: region.Y, DetectedAt: item.DetectedAt}
	seen := make(map[player.ID]bool)
	for _, target := range structures {
		id := player.ID(target.OwnerID)
		if id == observation.OwnerID || id == observation.CreatorID || seen[id] || !toweralert.ActiveTower(target) || world.WrappedManhattan(source.Tile, target.Tile) > 16 {
			continue
		}
		otherAlliance, _, err := r.social.FindByPlayer(ctx, id)
		if err != nil || otherAlliance.ID != share.allianceID {
			continue
		}
		if r.publishShared == nil {
			continue
		}
		if err := r.publishShared(id, shared); err != nil {
			return err
		}
		seen[id] = true
		r.shared[id] = append(r.shared[id], shared)
	}
	return nil
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

func (r *TowerAlertRepo) ListHistoryForPlayer(ctx context.Context, playerID player.ID, limit int, before time.Time, beforeID string) ([]toweralert.HistoryEntry, error) {
	owners, err := r.ListForPlayer(ctx, playerID, limit, before, beforeID)
	if err != nil {
		return nil, err
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	entries := make([]toweralert.HistoryEntry, 0, len(owners)+len(r.shared[playerID]))
	for i := range owners {
		item := owners[i]
		entries = append(entries, toweralert.HistoryEntry{Owner: &item})
	}
	for _, alert := range r.shared[playerID] {
		if !before.IsZero() && (alert.DetectedAt.After(before) || alert.DetectedAt.Equal(before) && alert.IncidentID >= beforeID) {
			continue
		}
		item := alert
		entries = append(entries, toweralert.HistoryEntry{Shared: &item})
	}
	sort.Slice(entries, func(i, j int) bool {
		var a, b time.Time
		var aid, bid string
		if entries[i].Shared != nil {
			a = entries[i].Shared.DetectedAt
			aid = entries[i].Shared.IncidentID
		} else {
			a = entries[i].Owner.DetectedAt
			aid = entries[i].Owner.IncidentID
		}
		if entries[j].Shared != nil {
			b = entries[j].Shared.DetectedAt
			bid = entries[j].Shared.IncidentID
		} else {
			b = entries[j].Owner.DetectedAt
			bid = entries[j].Owner.IncidentID
		}
		if a.Equal(b) {
			return aid > bid
		}
		return a.After(b)
	})
	if limit > 0 && len(entries) > limit {
		entries = entries[:limit]
	}
	return entries, nil
}

func (r *TowerAlertRepo) SetShare(ctx context.Context, towerID string, actor player.ID, allianceID alliance.ID, enabled bool) error {
	if r.buildings == nil || r.social == nil {
		return apperror.New(apperror.Internal, "tower sharing unavailable")
	}
	tower, err := r.buildings.FindByID(ctx, building.ID(towerID))
	if err != nil {
		return err
	}
	if tower.OwnerID != string(actor) {
		return apperror.New(apperror.Forbidden, "tower belongs to another player")
	}
	if tower.Type != building.TypeTower {
		return apperror.New(apperror.Validation, "building is not a tower")
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	share := r.shares[towerID]
	if !enabled {
		share.enabled = false
		share.version++
		r.shares[towerID] = share
		return nil
	}
	if tower.Level != 6 {
		return apperror.New(apperror.Validation, "sharing requires level six")
	}
	item, member, err := r.social.FindByPlayer(ctx, actor)
	if err != nil || item.ID != allianceID {
		return apperror.New(apperror.Forbidden, "alliance membership does not match")
	}
	share.allianceID = allianceID
	share.joinedAt = member.JoinedAt
	share.enabled = true
	share.version++
	r.shares[towerID] = share
	return nil
}

func (r *TowerAlertRepo) PublishSharedIfEligible(_ context.Context, _ string, _ func() error) (bool, error) {
	return false, nil
}
