package service

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"real-city/backend/internal/domain/action"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
	"real-city/backend/pkg/apperror"
)

// RaidService schedules a small attack against a nearby rival building.
type RaidService struct {
	buildings BuildingRepository
	actions   ActionRepository
	log       *slog.Logger
	resources *ResourceService
	events    *EventBus
	now       func() time.Time
}

type Raid struct {
	ID               action.ID     `json:"id"`
	AttackerID       player.ID     `json:"attacker_id"`
	TargetBuildingID building.ID   `json:"target_building_id"`
	Status           action.Status `json:"status"`
	Damage           int           `json:"damage"`
	DueAt            time.Time     `json:"due_at"`
	CreatedAt        time.Time     `json:"created_at"`
}

func NewRaidService(buildings BuildingRepository, actions ActionRepository, log *slog.Logger) *RaidService {
	return &RaidService{buildings: buildings, actions: actions, log: log, now: func() time.Time { return time.Now().UTC() }}
}

func (s *RaidService) SetResources(resources *ResourceService) { s.resources = resources }
func (s *RaidService) SetEventBus(events *EventBus)            { s.events = events }

func (s *RaidService) Start(ctx context.Context, attacker player.ID, targetID building.ID) (Raid, error) {
	if targetID == "" {
		return Raid{}, apperror.New(apperror.Validation, "target_building_id is required")
	}
	target, err := s.buildings.FindByID(ctx, targetID)
	if err != nil {
		return Raid{}, err
	}
	if target.OwnerID == string(attacker) {
		return Raid{}, apperror.New(apperror.Forbidden, "cannot raid your own building")
	}
	if target.Health <= 0 || (target.State != building.StateActive && target.State != building.StateDamaged) {
		return Raid{}, apperror.New(apperror.Conflict, "target building is unavailable")
	}
	inRange, err := s.inRange(ctx, attacker, target)
	if err != nil {
		return Raid{}, err
	}
	if !inRange {
		return Raid{}, apperror.New(apperror.Forbidden, "no active owned building in raid range")
	}
	now := s.now()
	rules := catalog.RaidRules()
	recent, err := s.actions.HasRecentRaid(ctx, attacker, targetID, now.Add(-time.Duration(rules.RaidCooldownSeconds)*time.Second))
	if err != nil {
		return Raid{}, err
	}
	if recent {
		return Raid{}, apperror.New(apperror.Conflict, "raid cooldown is active")
	}
	item := action.NewGameAction(action.ID(fmt.Sprintf("raid_%d_%s", now.UnixNano(), attacker)), action.TypeResolveRaid,
		fmt.Sprintf("raid:%s:%s:%d", attacker, targetID, now.Unix()/int64(rules.RaidCooldownSeconds)),
		action.ObjectRef{ID: string(attacker), Type: "player"}, action.ObjectRef{ID: string(targetID), Type: "building"},
		now.Add(time.Duration(rules.RaidTravelSeconds)*time.Second), now)
	item.Payload = []byte(`{}`)
	created, err := s.actions.AppendUnique(ctx, item)
	if err != nil {
		return Raid{}, err
	}
	if !created {
		return Raid{}, apperror.New(apperror.Conflict, "raid cooldown is active")
	}
	s.log.Info("raid.started", "attacker_id", attacker, "target_id", targetID, "raid_id", item.ID)
	return raidFromAction(item), nil
}

func (s *RaidService) List(ctx context.Context, attacker player.ID) ([]Raid, error) {
	items, err := s.actions.ListRaids(ctx, attacker)
	if err != nil {
		return nil, err
	}
	raids := make([]Raid, 0, len(items))
	for _, item := range items {
		raids = append(raids, raidFromAction(item))
	}
	return raids, nil
}

func (s *RaidService) Resolve(ctx context.Context, item action.GameAction, now time.Time) error {
	target, err := s.buildings.FindByID(ctx, building.ID(item.Target.ID))
	if err != nil {
		var appErr *apperror.Error
		if errors.As(err, &appErr) && appErr.Kind == apperror.NotFound {
			return nil
		} // Sold before arrival.
		return err
	}
	if target.Health <= 0 || target.State == building.StateRuined || target.OwnerID == item.Actor.ID {
		return nil
	}
	inRange, err := s.inRange(ctx, player.ID(item.Actor.ID), target)
	if err != nil {
		return err
	}
	if !inRange {
		return nil
	}
	damaged, applied, err := s.buildings.DamageIfCurrent(ctx, target.ID, target.Health, catalog.RaidRules().RaidDamage, now)
	if err != nil {
		return err
	}
	if !applied {
		return fmt.Errorf("raid target changed concurrently")
	}
	removed := damaged.State == building.StateRuined && (damaged.Type == building.TypeOilWell || catalog.IsRuin(damaged.Type))
	if removed {
		if damaged.Type == building.TypeOilWell && s.resources != nil {
			if err := s.resources.CancelOilJobs(ctx, damaged); err != nil {
				return err
			}
		}
		if err := s.buildings.Delete(ctx, damaged.ID); err != nil {
			return err
		}
		if damaged.Type == building.TypeOilWell && s.resources != nil {
			if err := s.resources.ReleaseOilWell(ctx, damaged.Tile, damaged.OwnerID); err != nil {
				return err
			}
		}
	}
	if s.events != nil {
		eventType := EventBuildingUpdated
		var payload any = BuildingPayload{Building: damaged, Reason: "raid"}
		if removed {
			eventType, payload = EventBuildingRemoved, BuildingRemovedPayload{BuildingID: damaged.ID, Reason: "raid"}
		}
		s.events.Publish(Event{Type: eventType, ChunkID: world.ChunkID(damaged.MapID, world.ChunkForTile(damaged.Tile)), PlayerID: player.ID(damaged.OwnerID), Payload: payload})
	}
	return s.actions.MarkDone(ctx, item.ID, now)
}

func (s *RaidService) inRange(ctx context.Context, attacker player.ID, target building.Building) (bool, error) {
	items, err := s.buildings.ListByPlayer(ctx, attacker)
	if err != nil {
		return false, err
	}
	for _, item := range items {
		if item.Health > 0 && item.State == building.StateActive && item.MapID == target.MapID &&
			wrappedTileDistance(item.Tile.X, target.Tile.X) <= catalog.RaidRules().RaidRangeTiles &&
			wrappedTileDistance(item.Tile.Y, target.Tile.Y) <= catalog.RaidRules().RaidRangeTiles {
			return true, nil
		}
	}
	return false, nil
}

func raidFromAction(item action.GameAction) Raid {
	return Raid{ID: item.ID, AttackerID: player.ID(item.Actor.ID), TargetBuildingID: building.ID(item.Target.ID), Status: item.Status,
		Damage: catalog.RaidRules().RaidDamage, DueAt: item.DueAt, CreatedAt: item.CreatedAt}
}
