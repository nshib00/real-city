package player

import "time"

type AccountAudit struct {
	ID             string    `json:"id"`
	ActorID        ID        `json:"actor_id"`
	PlayerID       ID        `json:"player_id"`
	Status         Status    `json:"status"`
	Role           Role      `json:"role"`
	PreviousStatus Status    `json:"previous_status"`
	PreviousRole   Role      `json:"previous_role"`
	Reason         string    `json:"reason"`
	CreatedAt      time.Time `json:"created_at"`
}
