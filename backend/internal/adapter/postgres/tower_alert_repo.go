package postgres

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"time"

	outbox "real-city/backend/internal/domain/event"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
	"real-city/backend/internal/service"
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
			payload, err := json.Marshal(service.TowerThreatPayload{IncidentID: item.IncidentID, TowerID: item.TowerID, MonsterID: item.MonsterID, MonsterType: item.MonsterType, TileX: item.TileX, TileY: item.TileY, TargetBuildingID: item.TargetBuildingID, DetectedAt: now})
			if err != nil {
				return err
			}
			event := outbox.NewOutboxEvent(outbox.ID("tower-alert:"+item.IncidentID), string(service.EventTowerThreatDetected), item.IncidentID, payload, now)
			event.PlayerID = string(observation.OwnerID)
			if err := r.outbox.Append(txCtx, event); err != nil {
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
		SELECT i.id,i.tower_id,i.monster_id,i.monster_type,i.tile_x,i.tile_y,i.target_building_id,i.detected_at
		FROM tower_alert_recipients r JOIN tower_alert_incidents i ON i.id=r.incident_id
		WHERE r.player_id=$1 AND ($2::timestamptz IS NULL OR (r.detected_at,r.incident_id)<($2,$3))
		ORDER BY r.detected_at DESC,r.incident_id DESC LIMIT $4
	`, playerID, cursor, beforeID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]service.TowerAlert, 0)
	for rows.Next() {
		var item service.TowerAlert
		if err := rows.Scan(&item.IncidentID, &item.TowerID, &item.MonsterID, &item.MonsterType, &item.TileX, &item.TileY, &item.TargetBuildingID, &item.DetectedAt); err != nil {
			return nil, err
		}
		item.OwnerID = playerID
		items = append(items, item)
	}
	return items, rows.Err()
}
