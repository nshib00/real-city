package toweralert

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"time"

	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/player"
)

type Observation struct {
	OwnerID          player.ID
	TowerID          string
	MonsterID        string
	MonsterType      string
	TileX            int
	TileY            int
	TargetBuildingID string
	CreatorID        player.ID
	RelayTowerIDs    []string
}

type Alert struct {
	IncidentID       string    `json:"incident_id"`
	OwnerID          player.ID `json:"-"`
	TowerID          string    `json:"tower_id"`
	MonsterID        string    `json:"monster_id"`
	MonsterType      string    `json:"monster_type"`
	TileX            int       `json:"tile_x"`
	TileY            int       `json:"tile_y"`
	TargetBuildingID string    `json:"target_building_id"`
	RelayTowerIDs    []string  `json:"relay_tower_ids"`
	DetectedAt       time.Time `json:"detected_at"`
}

// SharedAlert has no exact location or object identifiers.
type SharedAlert struct {
	IncidentID  string    `json:"incident_id"`
	MonsterType string    `json:"monster_type"`
	RegionX     int       `json:"region_x"`
	RegionY     int       `json:"region_y"`
	DetectedAt  time.Time `json:"detected_at"`
}

type HistoryEntry struct {
	Owner  *Alert
	Shared *SharedAlert
}

func (e HistoryEntry) MarshalJSON() ([]byte, error) {
	if e.Shared != nil {
		return json.Marshal(e.Shared)
	}
	return json.Marshal(e.Owner)
}

type State struct {
	Inside   bool
	LastSent time.Time
	Episode  int64
}

func Advance(state State, now time.Time) (State, bool) {
	if state.Inside {
		return state, false
	}
	state.Inside = true
	if !state.LastSent.IsZero() && now.Sub(state.LastSent) < time.Minute {
		return state, false
	}
	state.Episode++
	state.LastSent = now
	return state, true
}

func IncidentID(mapID string, ownerID player.ID, monsterID string, episode int64) string {
	key, _ := json.Marshal([]any{mapID, ownerID, monsterID, episode})
	sum := sha256.Sum256(key)
	return hex.EncodeToString(sum[:16])
}

func ActiveTower(tower building.Building) bool {
	if tower.Type != building.TypeTower || !tower.TowerWatchkeeperAssigned || tower.OwnerID == "" || tower.Level < 1 || tower.Level > 6 ||
		(tower.State != building.StateActive && tower.State != building.StateDamaged) {
		return false
	}
	spec, ok := catalog.GetBuilding(building.TypeTower)
	if !ok {
		return false
	}
	for _, level := range spec.UpgradeLevels {
		if level.Level == tower.Level {
			return level.Health > 0 && tower.Health*4 > level.Health
		}
	}
	return false
}
