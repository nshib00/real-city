package simulation

import (
	"context"
	"sort"
	"sync"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/toweralert"
	"real-city/backend/internal/domain/world"
	"real-city/backend/internal/service"
)

var towerRadii = [...]int{6, 8, 10, 12, 14, 16}
var towerRelayRadii = [...]int{0, 0, 0, 8, 12, 16}

const towerAlertCooldown = time.Minute
const towerScanInterval = 5 * time.Second

type towerThreatKey struct {
	monster monster.ID
	owner   string
}

type towerThreatState struct {
	inside   bool
	lastSent time.Time
}

// TowerDetector observes server-owned monster targets after the monster AI tick.
// State is kept per running simulation; reconnects do not create extra alerts.
type TowerDetector struct {
	mu        sync.Mutex
	buildings service.BuildingRepository
	monsters  service.MonsterRepository
	events    *service.EventBus
	alerts    service.TowerAlertRepository
	direct    bool
	seen      map[towerThreatKey]towerThreatState
	nextScan  time.Time
}

func NewTowerDetector(buildings service.BuildingRepository, monsters service.MonsterRepository, events *service.EventBus) *TowerDetector {
	return &TowerDetector{buildings: buildings, monsters: monsters, events: events, seen: make(map[towerThreatKey]towerThreatState)}
}

// Memory storage uses direct delivery; PostgreSQL stores a durable outbox event.
func (d *TowerDetector) SetAlertRepository(repo service.TowerAlertRepository, direct bool) {
	d.alerts = repo
	d.direct = direct
}

func (d *TowerDetector) Tick(ctx context.Context, now time.Time) (int, error) {
	d.mu.Lock()
	defer d.mu.Unlock()
	if now.Before(d.nextScan) {
		return 0, nil
	}
	var generation int64
	if d.alerts != nil {
		var err error
		generation, err = d.alerts.BeginScan(ctx, service.DefaultWorldID)
		if err != nil {
			return 0, err
		}
	}
	structures, err := d.buildings.ListByMap(ctx, service.DefaultWorldID)
	if err != nil {
		return 0, err
	}
	byID := make(map[building.ID]building.Building, len(structures))
	towers := make(map[string][]building.Building)
	for _, structure := range structures {
		byID[structure.ID] = structure
		if toweralert.ActiveTower(structure) {
			towers[structure.OwnerID] = append(towers[structure.OwnerID], structure)
		}
	}
	for owner := range towers {
		sort.Slice(towers[owner], func(i, j int) bool {
			a, b := towers[owner][i], towers[owner][j]
			if a.Level != b.Level {
				return a.Level > b.Level
			}
			if a.CreatedAt.Equal(b.CreatedAt) {
				return a.ID < b.ID
			}
			return a.CreatedAt.Before(b.CreatedAt)
		})
	}
	if len(towers) == 0 {
		if d.alerts != nil {
			if _, err := d.alerts.Reconcile(ctx, service.DefaultWorldID, generation, now, nil); err != nil {
				return 0, err
			}
		}
		clear(d.seen)
		d.nextScan = now.Add(towerScanInterval)
		return 0, nil
	}
	creatures, err := d.monsters.ListByMap(ctx, service.DefaultWorldID)
	if err != nil {
		return 0, err
	}
	inside := make(map[towerThreatKey]bool)
	observations := make([]service.TowerObservation, 0)
	sent := 0
	for _, creature := range creatures {
		if !creature.Alive() || creature.TargetType != "building" || creature.TargetID == "" ||
			(creature.State != monster.StateAggro && creature.State != monster.StateAttacking) {
			continue
		}
		target, ok := byID[building.ID(creature.TargetID)]
		if !ok || target.MapID != creature.MapID || target.OwnerID == "" ||
			target.State == building.StatePlanned || target.State == building.StateRuined || target.Health <= 0 ||
			building.IsTrapType(target.Type) || target.OwnerID == creature.CreatorID {
			continue
		}
		key := towerThreatKey{monster: creature.ID, owner: target.OwnerID}
		for _, tower := range towers[target.OwnerID] {
			if tower.MapID != creature.MapID || world.WrappedManhattan(tower.Tile, creature.Tile) > towerRadii[tower.Level-1] {
				continue
			}
			inside[key] = true
			if d.alerts != nil {
				observations = append(observations, service.TowerObservation{
					OwnerID: player.ID(target.OwnerID), TowerID: string(tower.ID), MonsterID: string(creature.ID),
					MonsterType: string(creature.Type), TileX: creature.Tile.X, TileY: creature.Tile.Y,
					TargetBuildingID: string(target.ID), RelayTowerIDs: towerRelayIDs(tower, towers[target.OwnerID]),
					CreatorID: player.ID(creature.CreatorID),
				})
				break
			}
			previous := d.seen[key]
			if previous.inside || now.Sub(previous.lastSent) < towerAlertCooldown {
				previous.inside = true
				d.seen[key] = previous
				break
			}
			if err := d.events.Publish(service.Event{
				Type: service.EventTowerThreatDetected, PlayerID: player.ID(target.OwnerID), CreatedAt: now,
				Payload: service.TowerThreatPayload{
					TowerID: string(tower.ID), MonsterID: string(creature.ID), MonsterType: string(creature.Type),
					TileX: creature.Tile.X, TileY: creature.Tile.Y, TargetBuildingID: string(target.ID), DetectedAt: now,
				},
			}); err != nil {
				return sent, err
			}
			d.seen[key] = towerThreatState{inside: true, lastSent: now}
			sent++
			break
		}
	}
	if d.alerts != nil {
		created, err := d.alerts.Reconcile(ctx, service.DefaultWorldID, generation, now, observations)
		if err != nil {
			return 0, err
		}
		if d.direct {
			for _, alert := range created {
				if err := d.events.Publish(service.Event{
					Type: service.EventTowerThreatDetected, PlayerID: alert.OwnerID, CreatedAt: alert.DetectedAt,
					Payload: service.TowerThreatPayload{
						IncidentID: alert.IncidentID, TowerID: alert.TowerID, MonsterID: alert.MonsterID,
						MonsterType: alert.MonsterType, TileX: alert.TileX, TileY: alert.TileY,
						TargetBuildingID: alert.TargetBuildingID, DetectedAt: alert.DetectedAt,
					},
				}); err != nil {
					return 0, err
				}
			}
		}
		d.nextScan = now.Add(towerScanInterval)
		return len(created), nil
	}
	for key, previous := range d.seen {
		if inside[key] {
			continue
		}
		if now.Sub(previous.lastSent) >= towerAlertCooldown {
			delete(d.seen, key)
		} else {
			previous.inside = false
			d.seen[key] = previous
		}
	}
	d.nextScan = now.Add(towerScanInterval)
	return sent, nil
}

func towerRelayIDs(source building.Building, active []building.Building) []string {
	if source.Level < 4 || source.Level > len(towerRelayRadii) {
		return nil
	}
	radius := towerRelayRadii[source.Level-1]
	ids := make([]string, 0)
	for _, target := range active {
		if target.ID != source.ID && target.MapID == source.MapID && world.WrappedManhattan(source.Tile, target.Tile) <= radius {
			ids = append(ids, string(target.ID))
		}
	}
	sort.Strings(ids)
	return ids
}

func towerActive(tower building.Building) bool { return toweralert.ActiveTower(tower) }
