package service

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/player"
)

const CombatRecordAction action.Type = "combat_record"

type CombatRecord struct {
	ID           string        `json:"id"`
	AttackerID   player.ID     `json:"attacker_id"`
	OwnerID      string        `json:"owner_id"`
	BuildingID   building.ID   `json:"building_id"`
	BuildingType building.Type `json:"building_type"`
	Level        int           `json:"level"`
	Damage       int           `json:"damage"`
	Destroyed    bool          `json:"destroyed"`
	XP           int           `json:"xp"`
	BaseXP       int           `json:"base_xp"`
	Source       string        `json:"source"`
	CreatedAt    time.Time     `json:"created_at"`
}

// Called inside the damage transaction: neither a journal row nor a private
// notification may survive a failed hit/reward/queue acknowledgement.
func (s *BuildingService) RecordBuildingAttack(ctx context.Context, before, after building.Building, attacker player.ID, source, id string, now time.Time) error {
	record := CombatRecord{ID: id, AttackerID: attacker, OwnerID: before.OwnerID, BuildingID: before.ID, BuildingType: before.Type, Level: before.Level, Damage: before.Health - after.Health, Destroyed: after.Health == 0, Source: source, CreatedAt: now}
	if record.Damage <= 0 {
		return nil
	}
	if record.Destroyed && attacker != "" && string(attacker) != before.OwnerID && before.OwnerID != "" {
		record.BaseXP = catalog.ExperienceForBuilding(before.Type, before.Level).Destruction
		if s.experience != nil {
			var err error
			record.XP, err = s.experience.players.XPEventAmount(ctx, attacker, fmt.Sprintf("building:%s:destroy", before.ID))
			if err != nil {
				return err
			}
		}
	}
	if s.actions != nil {
		item := action.NewGameAction(action.ID("combat_log:"+id), CombatRecordAction, "combat_log:"+id, action.ObjectRef{ID: string(attacker), Type: "player"}, action.ObjectRef{ID: string(before.ID), Type: "building"}, now, now)
		item.Status = action.StatusDone
		var err error
		item.Payload, err = json.Marshal(record)
		if err != nil {
			return err
		}
		created, err := s.actions.AppendUnique(ctx, item)
		if err != nil {
			return err
		}
		if !created {
			return nil
		}
	}
	for _, id := range []player.ID{attacker, player.ID(before.OwnerID)} {
		if id == "" || id == attacker && string(attacker) == before.OwnerID {
			continue
		}
		publishEvent(ctx, s.events, Event{Type: EventCombatResolved, PlayerID: id, Payload: record, CreatedAt: now})
	}
	return nil
}

func (s *CombatService) History(ctx context.Context, id player.ID, limit int) ([]CombatRecord, error) {
	records := []CombatRecord{}
	if s.actions == nil {
		return records, nil
	}
	if limit < 1 || limit > 100 {
		limit = 50
	}
	rows, err := s.actions.ListCombatRecords(ctx, id, limit)
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		var record CombatRecord
		if err := json.Unmarshal(row.Payload, &record); err != nil {
			return nil, err
		}
		records = append(records, record)
	}
	return records, nil
}
