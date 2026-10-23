package player

import "time"

type Presence struct {
	PlayerID  ID        `json:"player_id"`
	Name      string    `json:"name"`
	Level     int       `json:"level"`
	TileX     int       `json:"tile_x"`
	TileY     int       `json:"tile_y"`
	UpdatedAt time.Time `json:"-"`
}
