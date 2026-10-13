package action

import "time"

type ID string
type Status string
type Type string

const (
	StatusPending Status = "pending"
	StatusRunning Status = "running"
	StatusDone    Status = "done"
	StatusFailed  Status = "failed"

	TypeCompleteBuilding   Type = "complete_building"
	TypeCompleteProduction Type = "complete_production"
	TypeRespawnResource    Type = "respawn_resource"
	TypeRegrowForest       Type = "regrow_forest"
)

type ObjectRef struct {
	ID   string
	Type string
}

type GameAction struct {
	ID             ID
	Type           Type
	Status         Status
	IdempotencyKey string
	Actor          ObjectRef
	Target         ObjectRef
	Payload        []byte
	DueAt          time.Time
	LockedUntil    *time.Time
	Attempts       int
	LastError      string
	CreatedAt      time.Time
	UpdatedAt      time.Time
}

func NewGameAction(id ID, actionType Type, idempotencyKey string, actor ObjectRef, target ObjectRef, dueAt time.Time, now time.Time) GameAction {
	return GameAction{
		ID:             id,
		Type:           actionType,
		Status:         StatusPending,
		IdempotencyKey: idempotencyKey,
		Actor:          actor,
		Target:         target,
		DueAt:          dueAt,
		CreatedAt:      now,
		UpdatedAt:      now,
	}
}
