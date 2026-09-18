package event

import "time"

type ID string
type Status string

const (
	StatusPending Status = "pending"
	StatusSent    Status = "sent"
	StatusFailed  Status = "failed"
	StatusDead    Status = "dead"
)

type OutboxEvent struct {
	ID            ID
	Type          string
	AggregateID   string
	ChunkID       string
	PlayerID      string
	Alliance      string
	Payload       []byte
	Status        Status
	Attempts      int
	NextAttemptAt time.Time
	LockedUntil   *time.Time
	LastError     string
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

func NewOutboxEvent(id ID, eventType string, aggregateID string, payload []byte, now time.Time) OutboxEvent {
	return OutboxEvent{
		ID:            id,
		Type:          eventType,
		AggregateID:   aggregateID,
		Payload:       payload,
		Status:        StatusPending,
		NextAttemptAt: now,
		CreatedAt:     now,
		UpdatedAt:     now,
	}
}
