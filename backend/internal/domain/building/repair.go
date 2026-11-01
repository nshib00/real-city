package building

import "time"

type RepairJob struct {
	ID           string    `json:"id"`
	BuildingID   ID        `json:"building_id"`
	PlayerID     string    `json:"player_id"`
	BuildingType Type      `json:"building_type"`
	Level        int       `json:"level"`
	Workers      int       `json:"workers"`
	DueAt        time.Time `json:"due_at"`
	Status       string    `json:"status"`
}
