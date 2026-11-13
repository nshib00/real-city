package postgres

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"sort"
	"time"

	"real-city/backend/internal/domain/alliance"
	"real-city/backend/internal/domain/building"
	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type TowerAlertRepo struct {
	db     *sql.DB
	uow    *UnitOfWork
	outbox *OutboxRepo
}

func NewTowerAlertRepo(db *sql.DB) *TowerAlertRepo {
	return &TowerAlertRepo{db: db, uow: NewUnitOfWork(db), outbox: NewOutboxRepo(db)}
}

// BeginScan allocates a generation before world reads. An older snapshot cannot
// overwrite a newer generation, even when two simulation processes overlap.
func (r *TowerAlertRepo) BeginScan(ctx context.Context, mapID string) (int64, error) {
	var generation int64
	err := r.db.QueryRowContext(ctx, `
		INSERT INTO tower_alert_scans(map_id,next_generation) VALUES($1,1)
		ON CONFLICT(map_id) DO UPDATE SET next_generation=tower_alert_scans.next_generation+1
		RETURNING next_generation
	`, mapID).Scan(&generation)
	return generation, err
}

func (r *TowerAlertRepo) Reconcile(ctx context.Context, mapID string, generation int64, now time.Time, observations []service.TowerObservation) ([]service.TowerAlert, error) {
	created := make([]service.TowerAlert, 0)
	err := r.uow.Do(ctx, func(txCtx context.Context) error {
		exec := execer(txCtx, r.db)
		var next, applied int64
		if err := exec.QueryRowContext(txCtx, `SELECT next_generation,applied_generation FROM tower_alert_scans WHERE map_id=$1 FOR UPDATE`, mapID).Scan(&next, &applied); err != nil {
			return err
		}
		if generation <= applied || generation > next {
			return nil
		}
		seen := make(map[[2]string]bool, len(observations))
		for _, observation := range observations {
			key := [2]string{string(observation.OwnerID), observation.MonsterID}
			if seen[key] {
				continue
			}
			seen[key] = true
			state := toweralert.State{}
			var lastSent sql.NullTime
			err := exec.QueryRowContext(txCtx, `SELECT inside,last_sent_at,episode FROM tower_alert_state WHERE map_id=$1 AND owner_id=$2 AND monster_id=$3 FOR UPDATE`, mapID, observation.OwnerID, observation.MonsterID).Scan(&state.Inside, &lastSent, &state.Episode)
			if err != nil && !errors.Is(err, sql.ErrNoRows) {
				return err
			}
			if lastSent.Valid {
				state.LastSent = lastSent.Time
			}
			state, alert := toweralert.Advance(state, now)
			var sentAt any
			if !state.LastSent.IsZero() {
				sentAt = state.LastSent
			}
			if _, err := exec.ExecContext(txCtx, `
				INSERT INTO tower_alert_state(map_id,owner_id,monster_id,inside,last_sent_at,episode,seen_generation)
				VALUES($1,$2,$3,TRUE,$4,$5,$6)
				ON CONFLICT(map_id,owner_id,monster_id) DO UPDATE SET
				inside=TRUE,last_sent_at=EXCLUDED.last_sent_at,episode=EXCLUDED.episode,seen_generation=EXCLUDED.seen_generation
			`, mapID, observation.OwnerID, observation.MonsterID, sentAt, state.Episode, generation); err != nil {
				return err
			}
			if !alert {
				continue
			}
			item := service.TowerAlert{
				IncidentID: toweralert.IncidentID(mapID, observation.OwnerID, observation.MonsterID, state.Episode),
				OwnerID:    observation.OwnerID, TowerID: observation.TowerID, MonsterID: observation.MonsterID,
				MonsterType: observation.MonsterType, TileX: observation.TileX, TileY: observation.TileY,
				TargetBuildingID: observation.TargetBuildingID, DetectedAt: now,
			}
			if _, err := exec.ExecContext(txCtx, `
				INSERT INTO tower_alert_incidents(id,map_id,owner_id,monster_id,episode,tower_id,monster_type,tile_x,tile_y,target_building_id,detected_at)
				VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
			`, item.IncidentID, mapID, observation.OwnerID, observation.MonsterID, state.Episode, observation.TowerID, observation.MonsterType, observation.TileX, observation.TileY, observation.TargetBuildingID, now); err != nil {
				return err
			}
			if _, err := exec.ExecContext(txCtx, `INSERT INTO tower_alert_recipients(incident_id,player_id,detected_at) VALUES($1,$2,$3)`, item.IncidentID, observation.OwnerID, now); err != nil {
				return err
			}
			for _, relayID := range observation.RelayTowerIDs {
				if _, err := exec.ExecContext(txCtx, `INSERT INTO tower_alert_relays(incident_id,tower_id) VALUES($1,$2) ON CONFLICT DO NOTHING`, item.IncidentID, relayID); err != nil {
					return err
				}
			}
			payload, err := json.Marshal(service.TowerThreatPayload{IncidentID: item.IncidentID, TowerID: item.TowerID, MonsterID: item.MonsterID, MonsterType: item.MonsterType, TileX: item.TileX, TileY: item.TileY, TargetBuildingID: item.TargetBuildingID, DetectedAt: now})
			if err != nil {
				return err
			}
			event := outbox.NewOutboxEvent(outbox.ID("tower-alert:"+item.IncidentID), string(service.EventTowerThreatDetected), item.IncidentID, payload, now)
			event.PlayerID = string(observation.OwnerID)
			if err := r.outbox.Append(txCtx, event); err != nil {
				return err
			}
			if err := r.addSharedRecipients(txCtx, mapID, item, observation); err != nil {
				return err
			}
			created = append(created, item)
		}
		if _, err := exec.ExecContext(txCtx, `UPDATE tower_alert_state SET inside=FALSE WHERE map_id=$1 AND inside AND seen_generation<>$2`, mapID, generation); err != nil {
			return err
		}
		_, err := exec.ExecContext(txCtx, `UPDATE tower_alert_scans SET applied_generation=$2 WHERE map_id=$1`, mapID, generation)
		return err
	})
	if err != nil {
		return nil, err
	}
	return created, nil
}

func (r *TowerAlertRepo) ListForPlayer(ctx context.Context, playerID player.ID, limit int, before time.Time, beforeID string) ([]service.TowerAlert, error) {
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	var cursor any
	if !before.IsZero() {
		cursor = before
	}
	rows, err := r.db.QueryContext(ctx, `
		SELECT i.id,i.tower_id,i.monster_id,i.monster_type,i.tile_x,i.tile_y,i.target_building_id,i.detected_at,
			(SELECT COALESCE(json_agg(relay.tower_id ORDER BY relay.tower_id),'[]'::json) FROM tower_alert_relays relay WHERE relay.incident_id=i.id)
		FROM tower_alert_recipients r JOIN tower_alert_incidents i ON i.id=r.incident_id
		WHERE r.player_id=$1 AND r.scope='owner' AND ($2::timestamptz IS NULL OR (r.detected_at,r.incident_id)<($2,$3))
		ORDER BY r.detected_at DESC,r.incident_id DESC LIMIT $4
	`, playerID, cursor, beforeID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]service.TowerAlert, 0)
	for rows.Next() {
		var item service.TowerAlert
		var relays []byte
		if err := rows.Scan(&item.IncidentID, &item.TowerID, &item.MonsterID, &item.MonsterType, &item.TileX, &item.TileY, &item.TargetBuildingID, &item.DetectedAt, &relays); err != nil {
			return nil, err
		}
		if err := json.Unmarshal(relays, &item.RelayTowerIDs); err != nil {
			return nil, err
		}
		item.OwnerID = playerID
		items = append(items, item)
	}
	return items, rows.Err()
}

type towerShareRow struct {
	building building.Building
	alliance alliance.ID
	joinedAt time.Time
}

func scanTowerShare(row interface{ Scan(...any) error }) (towerShareRow, error) {
	var result towerShareRow
	err := row.Scan(&result.building.ID, &result.building.MapID, &result.building.OwnerID, &result.building.Type,
		&result.building.Level, &result.building.State, &result.building.Health, &result.building.Tile.X,
		&result.building.Tile.Y, &result.building.TowerWatchkeeperAssigned, &result.alliance, &result.joinedAt)
	return result, err
}

func (r *TowerAlertRepo) addSharedRecipients(ctx context.Context, mapID string, item service.TowerAlert, observation service.TowerObservation) error {
	exec := execer(ctx, r.db)
	source, err := scanTowerShare(exec.QueryRowContext(ctx, `
		SELECT b.id,b.map_id,b.owner_id,b.type,b.level,b.state,b.health,b.tile_x,b.tile_y,b.tower_watchkeeper_assigned,s.alliance_id,m.joined_at
		FROM buildings b JOIN tower_signal_shares s ON s.tower_id=b.id
		JOIN alliance_members m ON m.player_id=b.owner_id AND m.alliance_id=s.alliance_id AND m.joined_at=s.member_joined_at
		WHERE b.id=$1 AND s.enabled FOR SHARE OF b,s,m
	`, observation.TowerID))
	if errors.Is(err, sql.ErrNoRows) {
		return nil
	}
	if err != nil {
		return err
	}
	if source.building.OwnerID != string(observation.OwnerID) || source.building.MapID != mapID || source.building.Level != 6 || !toweralert.ActiveTower(source.building) {
		return nil
	}
	rows, err := exec.QueryContext(ctx, `
		SELECT b.id,b.map_id,b.owner_id,b.type,b.level,b.state,b.health,b.tile_x,b.tile_y,b.tower_watchkeeper_assigned,m.alliance_id,m.joined_at
		FROM buildings b JOIN alliance_members m ON m.player_id=b.owner_id
		WHERE m.alliance_id=$1 AND b.map_id=$2 AND b.owner_id<>$3 AND b.type='tower'
		ORDER BY b.owner_id,b.id FOR SHARE OF b,m
	`, source.alliance, mapID, observation.OwnerID)
	if err != nil {
		return err
	}
	selected := make(map[string]towerShareRow)
	for rows.Next() {
		candidate, err := scanTowerShare(rows)
		if err != nil {
			rows.Close()
			return err
		}
		if candidate.building.OwnerID == string(observation.CreatorID) || !toweralert.ActiveTower(candidate.building) ||
			world.WrappedManhattan(source.building.Tile, candidate.building.Tile) > 16 {
			continue
		}
		if _, exists := selected[candidate.building.OwnerID]; !exists {
			selected[candidate.building.OwnerID] = candidate
		}
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	region := world.ChunkForTile(world.Coord{X: item.TileX, Y: item.TileY})
	shared := toweralert.SharedAlert{IncidentID: item.IncidentID, MonsterType: item.MonsterType, RegionX: region.X, RegionY: region.Y, DetectedAt: item.DetectedAt}
	payload, err := json.Marshal(shared)
	if err != nil {
		return err
	}
	for recipientID, candidate := range selected {
		if _, err := exec.ExecContext(ctx, `
			INSERT INTO tower_alert_recipients(incident_id,player_id,detected_at,scope,relay_tower_id,alliance_id,share_version,recipient_joined_at,region_x,region_y)
			VALUES($1,$2,$3,'ally',$4,$5,(SELECT version FROM tower_signal_shares WHERE tower_id=$9),$6,$7,$8) ON CONFLICT DO NOTHING
		`, item.IncidentID, recipientID, item.DetectedAt, candidate.building.ID, source.alliance, candidate.joinedAt, region.X, region.Y, observation.TowerID); err != nil {
			return err
		}
		event := outbox.NewOutboxEvent(outbox.ID("tower-share:"+item.IncidentID+":"+recipientID), string(service.EventTowerThreatShared), item.IncidentID, payload, item.DetectedAt)
		event.PlayerID = recipientID
		if err := r.outbox.Append(ctx, event); err != nil {
			return err
		}
	}
	return nil
}

func (r *TowerAlertRepo) SetShare(ctx context.Context, towerID string, actor player.ID, allianceID alliance.ID, enabled bool) error {
	return r.uow.Do(ctx, func(txCtx context.Context) error {
		exec := execer(txCtx, r.db)
		var owner string
		var towerType building.Type
		var level int
		if err := exec.QueryRowContext(txCtx, `SELECT owner_id,type,level FROM buildings WHERE id=$1 FOR SHARE`, towerID).Scan(&owner, &towerType, &level); err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return apperror.New(apperror.NotFound, "tower not found")
			}
			return err
		}
		if owner != string(actor) {
			return apperror.New(apperror.Forbidden, "tower belongs to another player")
		}
		if towerType != building.TypeTower {
			return apperror.New(apperror.Validation, "building is not a tower")
		}
		if !enabled {
			_, err := exec.ExecContext(txCtx, `UPDATE tower_signal_shares SET enabled=FALSE,version=version+1,updated_at=now() WHERE tower_id=$1`, towerID)
			return err
		}
		if level != 6 {
			return apperror.New(apperror.Validation, "sharing requires level six")
		}
		var current alliance.ID
		var joinedAt time.Time
		if err := exec.QueryRowContext(txCtx, `SELECT alliance_id,joined_at FROM alliance_members WHERE player_id=$1 FOR SHARE`, actor).Scan(&current, &joinedAt); err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return apperror.New(apperror.Forbidden, "alliance membership required")
			}
			return err
		}
		if current != allianceID {
			return apperror.New(apperror.Forbidden, "alliance membership does not match")
		}
		_, err := exec.ExecContext(txCtx, `
			INSERT INTO tower_signal_shares(tower_id,alliance_id,enabled,member_joined_at) VALUES($1,$2,TRUE,$3)
			ON CONFLICT(tower_id) DO UPDATE SET alliance_id=EXCLUDED.alliance_id,enabled=TRUE,
				version=tower_signal_shares.version+1,member_joined_at=EXCLUDED.member_joined_at,updated_at=now()
		`, towerID, allianceID, joinedAt)
		return err
	})
}

// PublishSharedIfEligible holds the consent and membership rows until the
// shared event is accepted by the local event bus. A revoke or leave cannot
// cross this boundary without waiting for the check to finish.
func (r *TowerAlertRepo) PublishSharedIfEligible(ctx context.Context, eventID string, publish func() error) (bool, error) {
	published := false
	err := r.uow.Do(ctx, func(txCtx context.Context) error {
		exec := execer(txCtx, r.db)
		var source, target building.Building
		err := exec.QueryRowContext(txCtx, `
			SELECT src.id,src.map_id,src.owner_id,src.type,src.level,src.state,src.health,src.tile_x,src.tile_y,src.tower_watchkeeper_assigned,
				tgt.id,tgt.map_id,tgt.owner_id,tgt.type,tgt.level,tgt.state,tgt.health,tgt.tile_x,tgt.tile_y,tgt.tower_watchkeeper_assigned
			FROM outbox_events o
			JOIN tower_alert_recipients r ON r.incident_id=o.aggregate_id AND r.player_id=o.player_id AND r.scope='ally'
			JOIN tower_alert_incidents i ON i.id=r.incident_id
			JOIN buildings src ON src.id=i.tower_id
			JOIN tower_signal_shares s ON s.tower_id=src.id AND s.enabled AND s.alliance_id=r.alliance_id AND s.version=r.share_version
			JOIN alliance_members sm ON sm.player_id=src.owner_id AND sm.alliance_id=s.alliance_id AND sm.joined_at=s.member_joined_at
			JOIN buildings tgt ON tgt.id=r.relay_tower_id AND tgt.owner_id=r.player_id
			JOIN alliance_members tm ON tm.player_id=tgt.owner_id AND tm.alliance_id=s.alliance_id AND tm.joined_at=r.recipient_joined_at
			WHERE o.id=$1 AND o.type='tower.threat.shared' AND o.status='pending' AND r.delivered_at IS NULL
			FOR UPDATE OF r FOR SHARE OF i,src,s,sm,tgt,tm
		`, eventID).Scan(
			&source.ID, &source.MapID, &source.OwnerID, &source.Type, &source.Level, &source.State, &source.Health, &source.Tile.X, &source.Tile.Y, &source.TowerWatchkeeperAssigned,
			&target.ID, &target.MapID, &target.OwnerID, &target.Type, &target.Level, &target.State, &target.Health, &target.Tile.X, &target.Tile.Y, &target.TowerWatchkeeperAssigned,
		)
		if errors.Is(err, sql.ErrNoRows) {
			return nil
		}
		if err != nil {
			return err
		}
		if source.Level != 6 || !toweralert.ActiveTower(source) || !toweralert.ActiveTower(target) ||
			source.MapID != target.MapID || source.OwnerID == target.OwnerID || world.WrappedManhattan(source.Tile, target.Tile) > 16 {
			return nil
		}
		if err := publish(); err != nil {
			return err
		}
		if _, err := exec.ExecContext(txCtx, `UPDATE tower_alert_recipients SET delivered_at=now() WHERE incident_id=(SELECT aggregate_id FROM outbox_events WHERE id=$1) AND player_id=(SELECT player_id FROM outbox_events WHERE id=$1) AND scope='ally'`, eventID); err != nil {
			return err
		}
		published = true
		return nil
	})
	return published, err
}

func (r *TowerAlertRepo) ListHistoryForPlayer(ctx context.Context, playerID player.ID, limit int, before time.Time, beforeID string) ([]service.TowerAlertHistoryEntry, error) {
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	owners, err := r.ListForPlayer(ctx, playerID, limit, before, beforeID)
	if err != nil {
		return nil, err
	}
	var cursor any
	if !before.IsZero() {
		cursor = before
	}
	rows, err := r.db.QueryContext(ctx, `
		SELECT i.id,i.monster_type,r.region_x,r.region_y,r.detected_at
		FROM tower_alert_recipients r JOIN tower_alert_incidents i ON i.id=r.incident_id
		WHERE r.player_id=$1 AND r.scope='ally' AND r.delivered_at IS NOT NULL AND ($2::timestamptz IS NULL OR (r.detected_at,r.incident_id)<($2,$3))
		ORDER BY r.detected_at DESC,r.incident_id DESC LIMIT $4
	`, playerID, cursor, beforeID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	entries := make([]service.TowerAlertHistoryEntry, 0, len(owners))
	for i := range owners {
		item := owners[i]
		entries = append(entries, service.TowerAlertHistoryEntry{Owner: &item})
	}
	for rows.Next() {
		item := toweralert.SharedAlert{}
		if err := rows.Scan(&item.IncidentID, &item.MonsterType, &item.RegionX, &item.RegionY, &item.DetectedAt); err != nil {
			return nil, err
		}
		entries = append(entries, service.TowerAlertHistoryEntry{Shared: &item})
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	sort.Slice(entries, func(i, j int) bool {
		a, b := historyKey(entries[i]), historyKey(entries[j])
		if a.at.Equal(b.at) {
			return a.id > b.id
		}
		return a.at.After(b.at)
	})
	if len(entries) > limit {
		entries = entries[:limit]
	}
	return entries, nil
}

type towerHistoryKey struct {
	at time.Time
	id string
}

func historyKey(entry service.TowerAlertHistoryEntry) towerHistoryKey {
	if entry.Shared != nil {
		return towerHistoryKey{entry.Shared.DetectedAt, entry.Shared.IncidentID}
	}
	return towerHistoryKey{entry.Owner.DetectedAt, entry.Owner.IncidentID}
}
